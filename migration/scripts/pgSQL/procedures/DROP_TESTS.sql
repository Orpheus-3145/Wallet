CREATE OR REPLACE PROCEDURE w_data.DROP_TESTS(
	test_sequence_raw text default 'TEST'
)
LANGUAGE plpgsql AS $$
DECLARE
-- procedure variables
	id_to_drop int DEFAULT -1;
	test_sequence text default '';

BEGIN
	
	CREATE TEMP TABLE temp_ids (ID_TO_DROP INT);

	test_sequence = '%' || test_sequence_raw || '%';

	INSERT INTO temp_ids (ID_TO_DROP)
	SELECT ID
	FROM w_data.MOVIMENTI
	WHERE NOTE LIKE test_sequence;

	INSERT INTO temp_ids (ID_TO_DROP)
	SELECT ID_MOV
	FROM w_data.SPESE_VARIE
	WHERE DESCRIZIONE LIKE test_sequence;

	INSERT INTO temp_ids (ID_TO_DROP)
	SELECT ID_MOV
	FROM w_data.SPESE_FISSE
	WHERE DESCRIZIONE LIKE test_sequence;

	INSERT INTO temp_ids (ID_TO_DROP)
	SELECT ID_MOV
	FROM w_data.ENTRATE
	WHERE DESCRIZIONE LIKE test_sequence;

	INSERT INTO temp_ids (ID_TO_DROP)
	SELECT ID_MOV
	FROM w_data.DEBITI_CREDITI
	WHERE DESCRIZIONE LIKE test_sequence;

	INSERT INTO temp_ids (ID_TO_DROP)
	SELECT ID_MOV
	FROM w_data.SPESE_VIAGGI
	WHERE DESCRIZIONE LIKE test_sequence;

	INSERT INTO temp_ids (ID_TO_DROP)
	SELECT ID_MOV
	FROM w_data.SPESE_MANTENIMENTO
	WHERE DESCRIZIONE = 'TEST';

	FOR id_to_drop IN SELECT DISTINCT temp_ids.ID_TO_DROP from temp_ids
	LOOP
		
		CALL w_data.REMOVE_MOVEMENT(id_to_drop);

	END LOOP;

	DROP TABLE temp_ids;
END;
$$;