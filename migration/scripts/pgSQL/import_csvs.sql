DO $$
DECLARE
	csv_folder text := '../Wallet/migration/data/';
	csv_path text := '';
	table_name text := '';
	tables text[] := ARRAY[
		'MAP_TABELLE',
		'MAP_CONTI',
		'MAP_ENTRATE',
		'MAP_MOVIMENTI',
		'MAP_SPESE_VARIE',
		'WALLET_USERS',
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

	FOR table_name IN SELECT UNNEST(tables) LOOP

		csv_path = csv_folder || table_name || '.csv';
		-- import .csv into table
		EXECUTE format( $query$
			COPY public.%s
			FROM %L
			WITH (
				FORMAT csv,
				HEADER true,
				DELIMITER ','
			)
			$query$ , table_name, csv_path);

		-- update last index value counter
		EXECUTE format ( $query$ SELECT setval(pg_get_serial_sequence(%L, %L), MAX(%s)) 
			FROM %s
			$query$ , table_name, 'id', 'id', table_name);

	END LOOP;

END $$;