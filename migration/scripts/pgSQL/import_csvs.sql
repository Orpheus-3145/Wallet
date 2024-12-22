DO $$
DECLARE
	csv_folder text := '../Wallet/migration/data/';
	table_name text := '';
	map_schema_name text := 'w_map';
	data_schema_name text := 'w_data';
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
		'STIPENDI'
	];
BEGIN

	EXECUTE format(
		'SET search_path TO %s, %s'
	, map_schema_name, data_schema_name);

	FOR table_name IN SELECT UNNEST(tables) LOOP

		-- import .csv into table
		EXECUTE format( $query$
			COPY %s
			FROM %L
			WITH (
				FORMAT csv,
				HEADER true,
				DELIMITER ','
			)
			$query$ , table_name, csv_folder || table_name || '.csv');

		-- update last index value counter
		EXECUTE format (
			'SELECT setval(pg_get_serial_sequence(%L, %L), MAX(%s)) FROM %s'
		, table_name, 'id', 'id', table_name);

	END LOOP;

END $$;