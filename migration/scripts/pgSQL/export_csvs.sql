DO $$
DECLARE
	csv_folder text := '/var/lib/pgsql/17/Wallet/migration/data/test_exp/';
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

		EXECUTE format( $query$
			COPY %s
			TO %L
			WITH (
				FORMAT csv,
				HEADER true,
				DELIMITER ','
			)
			$query$ , table_name, csv_folder || table_name || '.csv');

	END LOOP;

END $$;