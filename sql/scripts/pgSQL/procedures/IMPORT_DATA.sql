CREATE OR REPLACE PROCEDURE w_data.IMPORT_DATA(
	csv_folder text
)
LANGUAGE plpgsql AS $$
DECLARE
  -- procedure variables
	table_name text := '';
	tables text[] := ARRAY[
		-- 'MAP_TABELLE',
		-- 'MAP_CONTI',
		-- 'MAP_ENTRATE',
		-- 'MAP_MOVIMENTI',
		-- 'MAP_SPESE_VARIE',
		'MOVIMENTI',
		'DEBITI_CREDITI',
		'ENTRATE',
		'SPESE_FISSE',
		'SPESE_MANTENIMENTO',
		'SPESE_VARIE',
		'SPESE_VIAGGI',
		'STIPENDI'];
BEGIN

	SET search_path TO w_data, w_map;

	FOR table_name IN SELECT UNNEST(tables) LOOP

		EXECUTE format( $query$
			COPY %s
			FROM %L
			WITH (
				FORMAT csv,
				HEADER true,
				DELIMITER '|'
			)
			$query$, table_name, csv_folder || table_name || '.csv');

		-- update last index value counter
		EXECUTE format (
			'SELECT setval(pg_get_serial_sequence(%L, %L), MAX(%s)) FROM %s'
		, table_name, 'id', 'id', table_name);

	END LOOP;

END $$;