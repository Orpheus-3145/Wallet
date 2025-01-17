CREATE OR REPLACE PROCEDURE w_data.EXPORT_DATA(
	csv_folder text default ''
)
LANGUAGE plpgsql AS $$
DECLARE
  -- procedure variables
	table_name text := '';
	tables text[] := ARRAY[
		'MAP_TABELLE',
		'MAP_CONTI',
		'MAP_ENTRATE',
		'MAP_MOVIMENTI',
		'MAP_SPESE_VARIE',
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
				TO %L
				WITH (
					FORMAT csv,
					HEADER true,
					DELIMITER '|'
				)
			$query$ , table_name, csv_folder || table_name || '.csv');

	END LOOP;

END $$;