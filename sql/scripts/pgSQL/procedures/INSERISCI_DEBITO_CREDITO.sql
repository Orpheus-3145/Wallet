CREATE OR REPLACE PROCEDURE w_data.INSERISCI_DEBITO_CREDITO(
	data_mov date,
	id_conto int,
	importo real,
	test boolean,
	deb_cred boolean,
	origine text,
	descrizione text,
	note text DEFAULT ''
)
LANGUAGE plpgsql AS $$
DECLARE
  -- procedure variables
	type_mov CONSTANT text DEFAULT 'Debito - Credito';
	id_tipo_mov integer DEFAULT -1;
	dare_avere boolean DEFAULT FALSE;
	id_mov_main int DEFAULT -1;

BEGIN
	IF deb_cred = FALSE THEN
		dare_avere = TRUE;
	ELSE
		dare_avere = FALSE;
	END IF;

	-- assigning id_tipo_mov
	SELECT ID INTO STRICT id_tipo_mov 
		FROM w_map.MAP_MOVIMENTI AS map_mov 
		WHERE map_mov.DESCRIZIONE = type_mov;

	if test = TRUE THEN
		origine = origine || ' |TEST|';
		descrizione = descrizione || ' |TEST|';
		note = note || ' |TEST|';
	END IF;

	-- inserting main mov
	INSERT INTO w_data.MOVIMENTI(ID_TIPO_MOV, ID_CONTO, DATA_INS, DATA_MOV, DARE_AVERE, IMPORTO, NOTE) 
		VALUES (id_tipo_mov, id_conto, CURRENT_TIMESTAMP, data_mov, dare_avere, importo, note);

	-- assigning id_mov_main
	SELECT ID INTO id_mov_main 
		FROM w_data.MOVIMENTI 
		ORDER BY ID DESC LIMIT 1; 

	-- inserting deb-cred mov
	INSERT INTO w_data.DEBITI_CREDITI (ID_MOV, DEB_CRED, ORIGINE, DESCRIZIONE, SALDATO, ID_MOV_SALDO, DATA_SALDO) 
		VALUES (id_mov_main, deb_cred, origine, descrizione, FALSE, NULL, NULL);

EXCEPTION
	WHEN NO_DATA_FOUND THEN
		RAISE EXCEPTION 'No movement found for type: %', type_mov USING HINT = 'Internal error';

END;
$$;
