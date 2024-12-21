CREATE USER w_user WITH LOGIN PASSWORD '82!eyh_dw';
-- it should also update table WALLET_USERS
GRANT CONNECT ON DATABASE wallet TO w_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO w_user;      -- not all tables: read everywhere, write only in movement tables
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.movimenti_id_seq TO w_user;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.spese_varie_id_seq TO w_user;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.spese_fisse_id_seq TO w_user;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.stipendi_id_seq TO w_user;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.entrate_id_seq TO w_user;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.debiti_crediti_id_seq TO w_user;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.spese_mantenimento_id_seq TO w_user;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.spese_viaggi_id_seq TO w_user;
