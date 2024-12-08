CREATE OR REPLACE PROCEDURE REMOVE_MOVEMENT(
	id_mov_to_drop int
)
LANGUAGE plpgsql AS $$
DECLARE
  	-- procedure variables
    id_tipo_mov int DEFAULT -1;
    id_table int DEFAULT -1;
    table_name text DEFAULT '';

BEGIN
    SELECT mv.ID_TIPO_MOV INTO STRICT id_tipo_mov FROM MOVIMENTI mv WHERE ID = id_mov_to_drop;
    SELECT mm.ID_TABLE INTO STRICT id_table FROM MAP_MOVIMENTI mm WHERE ID = id_tipo_mov;
    SELECT NOME INTO STRICT table_name FROM MAP_TABELLE WHERE ID = id_table;

    EXECUTE FORMAT('DELETE FROM %s WHERE ID_MOV = %s', table_name, id_mov_to_drop);
    DELETE FROM MOVIMENTI WHERE ID = id_mov_to_drop;

EXCEPTION
	WHEN NO_DATA_FOUND THEN
		RAISE EXCEPTION 'No table found for id move: %', id_mov_to_drop USING HINT = 'Internal error';
END;
$$;