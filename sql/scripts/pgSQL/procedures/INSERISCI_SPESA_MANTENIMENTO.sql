CREATE OR REPLACE PROCEDURE w_data.INSERISCI_SPESA_MANTENIMENTO(
	data_mov date,
	id_conto int,
	importo real,
	descrizione text,
	note text DEFAULT ''
)
LANGUAGE plpgsql AS $$
DECLARE

  	-- procedure variables
	type_mov CONSTANT text DEFAULT 'Spesa di Mantenimento';
	id_tipo_mov integer DEFAULT -1;
	dare_avere CONSTANT boolean DEFAULT FALSE;
	id_mov_main int DEFAULT -1;

BEGIN
    -- assigning id_tipo_mov
	SELECT ID INTO STRICT id_tipo_mov
		FROM w_map.MAP_MOVIMENTI AS map_mov 
		WHERE map_mov.DESCRIZIONE = type_mov;

	-- inserting main mov
	INSERT INTO w_data.MOVIMENTI(ID_TIPO_MOV, ID_CONTO, DATA_INS, DATA_MOV, DARE_AVERE, IMPORTO, NOTE) 
		VALUES (id_tipo_mov, id_conto, CURRENT_TIMESTAMP, data_mov, dare_avere, importo, note);

	-- assigning id_mov_main
	SELECT ID INTO id_mov_main 
		FROM w_data.MOVIMENTI 
		ORDER BY ID DESC LIMIT 1; 

    --inserting spesa di mantenimento
	INSERT INTO w_data.SPESE_MANTENIMENTO(ID_MOV, DESCRIZIONE) 
		VALUES (id_mov_main, descrizione);

EXCEPTION
	WHEN NO_DATA_FOUND THEN
		RAISE EXCEPTION 'No movement found for type: %', type_mov USING HINT = 'Internal error';

END;
$$;