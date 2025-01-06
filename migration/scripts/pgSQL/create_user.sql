BEGIN;

CREATE USER :user_db WITH LOGIN PASSWORD :'pwd_db';

-- user can connect db
GRANT CONNECT ON DATABASE wallet TO :user_db;

-- can access whatever on schema w_data
GRANT USAGE ON SCHEMA w_data TO :user_db;

-- can read/write every table of schema w_data
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA w_data TO :user_db;

-- and the id fields
GRANT SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA w_data TO :user_db;

-- can run every function/procedure of w_data
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA w_data TO :user_db;

-- can access whatever on schema w_map
GRANT USAGE ON SCHEMA w_map TO :user_db;

-- can read every table of schema w_map
GRANT SELECT ON ALL TABLES IN SCHEMA w_map TO :user_db;

-- set order of visibility
ALTER USER :user_db SET search_path TO w_data, w_map, public;

COMMIT;
