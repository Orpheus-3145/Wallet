CREATE OR REPLACE PROCEDURE INSERISCI_ENTRATA(
	data_mov date,
	id_conto int,
	importo real,
	id_tipo_entrata int,
	descrizione text,
	note text DEFAULT ''
)
LANGUAGE plpgsql AS $$
DECLARE

  -- procedure variables
	type_mov CONSTANT text DEFAULT 'Entrata';
	id_tipo_mov integer DEFAULT -1;
	dare_avere CONSTANT boolean DEFAULT TRUE;
	id_mov_main int DEFAULT -1;

BEGIN
    -- assigning id_tipo_mov
	SELECT ID INTO STRICT id_tipo_mov FROM MAP_MOVIMENTI AS map_mov WHERE map_mov.DESCRIZIONE = type_mov;

	-- inserting main mov
	INSERT INTO MOVIMENTI(ID_TIPO_MOV, ID_CONTO, DATA_INS, DATA_MOV, DARE_AVERE, IMPORTO, NOTE) VALUES (id_tipo_mov, id_conto, CURRENT_TIMESTAMP, data_mov, dare_avere, importo, note);

	-- assigning id_mov_main
	SELECT ID INTO id_mov_main FROM MOVIMENTI ORDER BY ID DESC LIMIT 1; 

    --inserting entrata
	INSERT INTO ENTRATE(ID_MOV, ID_TIPO_ENTRATA, DESCRIZIONE) VALUES (id_mov_main, id_tipo_entrata, descrizione);

EXCEPTION
	WHEN NO_DATA_FOUND THEN
		RAISE EXCEPTION 'No movement found for type: %', type_mov USING HINT = 'Internal error';

END;
$$;