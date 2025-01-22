BEGIN;

  -- user admin creation
  CREATE ROLE :admin_name WITH SUPERUSER LOGIN PASSWORD :'admin_pwd';

  CREATE ROLE :user_name WITH LOGIN PASSWORD :'user_pwd';

  -- user can connect db
  GRANT CONNECT ON DATABASE wallet TO :user_name;

  -- can access whatever on schema w_data
  GRANT USAGE ON SCHEMA w_data TO :user_name;

  -- can read/write every table of schema w_data
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA w_data TO :user_name;

  -- and the id fields
  GRANT SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA w_data TO :user_name;

  -- and for every new entity created
  ALTER DEFAULT PRIVILEGES IN SCHEMA w_data GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :user_name;
  ALTER DEFAULT PRIVILEGES IN SCHEMA w_data GRANT SELECT, UPDATE ON SEQUENCES TO :user_name;

  -- can run every function/procedure of w_data
  GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA w_data TO :user_name;

  -- can access whatever on schema w_map
  GRANT USAGE ON SCHEMA w_map TO :user_name;

  -- can read every table of schema w_map
  GRANT SELECT ON ALL TABLES IN SCHEMA w_map TO :user_name;

  -- and the id fields
  GRANT SELECT ON ALL SEQUENCES IN SCHEMA w_map TO :user_name;

  -- and for every new entity created
  ALTER DEFAULT PRIVILEGES IN SCHEMA w_map GRANT SELECT ON TABLES TO :user_name;
  ALTER DEFAULT PRIVILEGES IN SCHEMA w_map GRANT SELECT ON SEQUENCES TO :user_name;

  -- set order of visibility
  ALTER USER :user_name SET search_path TO w_data, w_map, public;

COMMIT;
