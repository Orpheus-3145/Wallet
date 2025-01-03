-- \set map_schema :'w_map'
-- \set data_schema :'w_data'
-- \set user :'fra'
-- \set pwd :'91913881'


DO $$
DECLARE
	map_schema_name text := :map_schema;
	data_schema_name text := :data_schema;
	user_name text := :user;
	user_pwd text := :pwd;
BEGIN

	EXECUTE format(
		'CREATE USER %s WITH LOGIN PASSWORD %L'
		, user_name, user_pwd);

	-- user can connect db
	EXECUTE format( 
		'GRANT CONNECT ON DATABASE wallet TO %s'
		, user_name);

	-- can access whatever on schema w_data
	EXECUTE format( 
		'GRANT USAGE ON SCHEMA %s TO %s'
		, data_schema_name, user_name);

	-- can read/write every table of schema w_data
	EXECUTE format( 
		'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %s TO %s'
		, data_schema_name, user_name);

    -- and the id fields
	EXECUTE format( 
		'GRANT SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA %s TO %s'
		, data_schema_name, user_name);

	-- can run every function/procedure of w_data
	EXECUTE format( 
		'GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA %s TO %s'
		, data_schema_name, user_name);

	-- can access whatever on schema w_map
	EXECUTE format( 
		'GRANT USAGE ON SCHEMA %s TO %s'
		, map_schema_name, user_name);
	
	-- can read every table of schema w_map
	EXECUTE format( 
		'GRANT SELECT ON ALL TABLES IN SCHEMA %s TO %s'
		, map_schema_name, user_name);
    
	-- set order of visibility
	EXECUTE format( 
		'ALTER USER %s SET search_path TO %s, %s, public;'
		, user_name, data_schema_name, map_schema_name);
	
END $$;
