DO $$
DECLARE
	csv_folder text := '/var/lib/pgsql/17/Wallet/migration/data/test_exp/';
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
		EXECUTE format( $query$
			COPY public.%s
			TO %L
			WITH (
				FORMAT csv,
				HEADER true,
				DELIMITER ','
			)
			$query$ , table_name, csv_path);

	END LOOP;

END $$;