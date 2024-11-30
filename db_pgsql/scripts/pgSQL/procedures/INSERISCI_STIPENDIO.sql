CREATE OR REPLACE PROCEDURE INSERISCI_STIPENDIO(
	data_mov date,
	id_conto int,
	importo real,
	ddl text,
	note text DEFAULT '',
	netto real DEFAULT 0,
	rimborso_spese real DEFAULT 0
)
LANGUAGE plpgsql AS $$
DECLARE
  	-- procedure variables
	type_mov CONSTANT text DEFAULT 'Stipendio';
	id_tipo_mov integer DEFAULT -1;
	dare_avere CONSTANT boolean DEFAULT TRUE;
	id_mov_main int DEFAULT -1;
	previous_month int DEFAULT EXTRACT(MONTH FROM data_mov::DATE) - 1;
    trattenute real DEFAULT 0;

BEGIN
	IF importo < netto THEN
        RAISE 'Invalid input: netto [%] has to be equal of less than importo [%]', netto, importo;
	ELSIF importo < rimborso_spese THEN
        RAISE 'Invalid input: rimborso spese [%] has to be equal of less than importo [%]', rimborso_spese, importo;
	END IF;

    IF previous_month = 0 THEN
        previous_month = 12;
    END IF;

    IF netto = 0 THEN
        netto = importo;
    END IF;

    IF importo > (netto + rimborso_spese) THEN
        trattenute = importo - netto - rimborso_spese;
    END IF;

    -- assigning id_tipo_mov
	SELECT ID INTO STRICT id_tipo_mov FROM MAP_MOVIMENTI AS map_mov WHERE map_mov.DESCRIZIONE = type_mov;

	-- inserting main mov
	INSERT INTO MOVIMENTI(ID_TIPO_MOV, ID_CONTO, DATA_INS, DATA_MOV, DARE_AVERE, IMPORTO, NOTE) VALUES (id_tipo_mov, id_conto, CURRENT_TIMESTAMP, data_mov, dare_avere, importo, note);

	-- assigning id_mov_main
	SELECT ID INTO id_mov_main FROM MOVIMENTI ORDER BY ID DESC LIMIT 1; 

    --inserting stipendio
	INSERT INTO STIPENDI(ID_MOV, DDL, MESE, NETTO, TOTALE, TRATTENUTE, RIMBORSO_SPESE) VALUES (id_mov_main, ddl, previous_month, netto, importo, trattenute, rimborso_spese);

EXCEPTION
	WHEN NO_DATA_FOUND THEN
		RAISE EXCEPTION 'No movement found for type: %', type_mov USING HINT = 'Internal error';

	WHEN TOO_MANY_ROWS THEN
		RAISE EXCEPTION 'Too many movements found for type: %', type_mov USING HINT = 'Internal error';

END;
$$;