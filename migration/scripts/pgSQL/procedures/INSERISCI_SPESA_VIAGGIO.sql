CREATE OR REPLACE PROCEDURE INSERISCI_SPESA_VIAGGIO(
	data_mov date,
	id_conto int,
	importo real,
	viaggio text,
	descrizione text,
	note text DEFAULT ''
)
LANGUAGE plpgsql AS $$
DECLARE
  	-- procedure variables
	type_mov CONSTANT text DEFAULT 'Spesa di Viaggio';
	id_tipo_mov integer DEFAULT -1;
	dare_avere CONSTANT boolean DEFAULT FALSE;
	id_mov_main int DEFAULT -1;

BEGIN
    -- assigning id_tipo_mov
	SELECT ID INTO STRICT id_tipo_mov FROM MAP_MOVIMENTI AS map_mov WHERE map_mov.DESCRIZIONE = type_mov;

	-- inserting main mov
	INSERT INTO MOVIMENTI(ID_TIPO_MOV, ID_CONTO, DATA_INS, DATA_MOV, DARE_AVERE, IMPORTO, NOTE) VALUES (id_tipo_mov, id_conto, CURRENT_TIMESTAMP, data_mov, dare_avere, importo, note);

	-- assigning id_mov_main
	SELECT ID INTO id_mov_main FROM MOVIMENTI ORDER BY ID DESC LIMIT 1; 

    --inserting spesa di viaggio
    INSERT INTO SPESE_VIAGGI(ID_MOV, VIAGGIO, DESCRIZIONE) VALUES (id_mov_main, viaggio, descrizione);

EXCEPTION
	WHEN NO_DATA_FOUND THEN
		RAISE EXCEPTION 'No movement found for type: %', type_mov USING HINT = 'Internal error';

END;
$$;