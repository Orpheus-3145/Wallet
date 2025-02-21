CREATE OR REPLACE PROCEDURE w_data.SALDA_DEBITO_CREDITO(
    data_mov date,
    id_conto integer,
		test boolean,
    id_saldo_deb_cred integer[],
    note text DEFAULT '',
    importo real DEFAULT 0
)
LANGUAGE plpgsql AS $$
DECLARE
    -- procedure variables
	manually_close boolean DEFAULT FALSE;
	type_mov CONSTANT text DEFAULT 'Saldo Debito - Credito';
	id_tipo_mov integer DEFAULT -1;
	dare_avere boolean DEFAULT TRUE;
	tot_importo real DEFAULT 0.0;
	origine text DEFAULT '';
	id_mov_main int DEFAULT -1;
	id_mov_opt int = 0;
	diff real = 0;
	curr_importo int = 0;
	current_id int = -1;

BEGIN
    -- split behaviour into simpler procedures

	IF array_length(id_saldo_deb_cred, 1) = 0 THEN
		RAISE EXCEPTION 'No input ids to close';
	END IF;

	-- se é stato passato manualmente un importo, allora il saldo devo riguardare solo debiti o solo crediti
	IF importo <> 0 THEN
		IF (
			SELECT count(DISTINCT dc.DEB_CRED) 
				FROM w_data.DEBITI_CREDITI dc 
				WHERE ID_MOV = ANY (id_saldo_deb_cred)
			) > 1 THEN
			RAISE EXCEPTION 'Selezionati debiti e crediti in contemporanea da saldare in modo parziale';
		END IF;
		manually_close = TRUE;
	END IF;

	-- controllo di non considerare movimenti gia' saldati
	IF (
		SELECT count(*)
			FROM w_data.DEBITI_CREDITI dc
			WHERE ID_MOV = ANY (id_saldo_deb_cred) AND SALDATO = TRUE
		) > 0 THEN
		RAISE EXCEPTION 'Selezionati debiti e crediti gia'' saldati';
	END IF;

	-- importo totale da saldare dei deb/cred selezionati
	SELECT CAST(SUM(CASE WHEN mv.DARE_AVERE = TRUE THEN mv.IMPORTO * -1 ELSE mv.IMPORTO END) AS DECIMAL(9,2))
		INTO tot_importo 
		FROM w_data.MOVIMENTI mv
		WHERE mv.ID = ANY (id_saldo_deb_cred);

	-- origine comune dei deb/cred selezionati
	BEGIN
		SELECT DISTINCT dc.ORIGINE
			INTO STRICT origine 
			FROM w_data.DEBITI_CREDITI dc
			WHERE dc.ID_MOV = ANY (id_saldo_deb_cred);
	EXCEPTION
		WHEN TOO_MANY_ROWS THEN
			RAISE EXCEPTION 'Selezionati deb/cred da diversa origine % ' , id_saldo_deb_cred;
	END;
	
	-- assigning id_tipo_mov
	SELECT map_mov.ID 
		INTO STRICT id_tipo_mov 
		FROM w_map.MAP_MOVIMENTI AS map_mov 
		WHERE map_mov.DESCRIZIONE = type_mov;

	-- dare-avere del futuro movimento
	IF tot_importo < 0 THEN
		dare_avere = FALSE;
		tot_importo = tot_importo * -1;
	END IF;

	IF manually_close THEN
		IF importo > tot_importo THEN
			diff = importo - tot_importo;
		ELSE 
			tot_importo = importo;
		END IF;
	END IF;

	if test = TRUE THEN
		note = note || ' |TEST|';
	END IF;

	-- inserting main mov
	INSERT INTO w_data.MOVIMENTI(ID_TIPO_MOV, 
									ID_CONTO,
									DATA_INS,
									DATA_MOV,
									DARE_AVERE,
									IMPORTO,
									NOTE) 
	VALUES (id_tipo_mov,
			id_conto,
			CURRENT_TIMESTAMP,
			data_mov,
			dare_avere,
			tot_importo,
			note || ' -- Saldo id:');

	-- assigning id_mov_main
	SELECT ID INTO id_mov_main 
		FROM w_data.MOVIMENTI
		ORDER BY ID DESC LIMIT 1; 

	FOREACH current_id IN ARRAY id_saldo_deb_cred 
	LOOP

		-- add id of deb/cred(s) closed
		UPDATE w_data.MOVIMENTI SET 
			NOTE = MOVIMENTI.NOTE || ' ' || CAST(current_id AS text)
		WHERE ID = id_mov_main;

		IF manually_close = FALSE THEN
			UPDATE w_data.DEBITI_CREDITI SET 
				SALDATO = TRUE, 
				ID_MOV_SALDO = COALESCE(ID_MOV_SALDO || ' ', '') || CAST(id_mov_main AS text),
				DATA_SALDO = data_mov 
			WHERE ID_MOV = current_id;
		ELSE
			SELECT mv.IMPORTO 
				INTO STRICT curr_importo 
				FROM w_data.MOVIMENTI mv
				WHERE ID = current_id;

			IF importo >= curr_importo THEN
				importo = importo - curr_importo;
				
				UPDATE w_data.DEBITI_CREDITI SET 
					SALDATO = TRUE, 
					ID_MOV_SALDO = COALESCE(ID_MOV_SALDO || ' ', '') || CAST(id_mov_main AS text),
					DATA_SALDO = data_mov 
				WHERE ID_MOV = current_id;

				IF importo = 0 THEN
					EXIT;
				END IF;
			ELSE
				-- in questo caso non riesco a saldare lo specifico deb/cred, modifico l'importo di quello che riesco a saldare ed esco dal loop
				UPDATE w_data.DEBITI_CREDITI SET 
					ID_MOV_SALDO = COALESCE(ID_MOV_SALDO || ' ', '') || CAST(id_mov_main AS text)
				WHERE ID_MOV = current_id;

				UPDATE w_data.MOVIMENTI SET 
					NOTE = MOVIMENTI.NOTE || ' [partial]'
				WHERE ID = id_mov_main;

				UPDATE w_data.MOVIMENTI SET 
					NOTE = COALESCE(MOVIMENTI.NOTE || ' - ', '') || 'importo originale ' || CAST(curr_importo AS text) || ', ridotto a ' || CAST(curr_importo - SALDA_DEBITO_CREDITO.importo AS text) || ' a seguito del saldo parziale di ' || CAST(SALDA_DEBITO_CREDITO.importo AS text) || ', compreso nel movimento id: ' || CAST(id_mov_main AS text),
					IMPORTO = curr_importo - SALDA_DEBITO_CREDITO.importo
				WHERE ID = current_id;
				
				EXIT;
			END IF;
		END IF;
	END LOOP;

	-- se diff > 0 allora viene creato un altro debito/credito oltre al saldo, che rappresenta il credito/debito che tiene conto dell'avanzo, che a sua volta dovrà essere saldato
	IF diff > 0 THEN
		CALL w_data.INSERISCI_DEBITO_CREDITO(data_mov,
										id_conto,
										diff,
										NOT dare_avere,
										origine,
										'Eccesso del saldo id: ' || CAST(id_mov_main AS text),
										note); 
	END IF;
END;
$$;
