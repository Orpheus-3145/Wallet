\copy public.map_tabelle(id, id_ruolo, nome, descrizione) 
FROM './wallet/data/MAP_TABELLE.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.map_conti(id, tipo, descrizione) 
FROM './wallet/data/MAP_CONTI.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.map_entrate(id, descrizione) 
FROM './wallet/data/MAP_ENTRATE.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);


\copy public.map_movimenti(id, id_table, descrizione, stored_procedure) 
FROM './wallet/data/MAP_MOVIMENTI.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.map_spese_varie(id, descrizione) 
FROM './wallet/data/MAP_SPESE_VARIE.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.wallet_users(id, username, password, note) 
FROM './wallet/data/WALLET_USERS.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.movimenti(id, data_mov, data_ins, importo, dare_avere, id_tipo_mov, id_conto, note) 
FROM './wallet/data/MOVIMENTI.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);
\copy public.debiti_crediti(id, id_mov, deb_cred, descrizione, origine, saldato, id_mov_saldo, data_saldo) 
FROM './wallet/data/DEBITI_CREDITI.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.entrate(id, id_mov, id_tipo_entrata, descrizione) 
FROM './wallet/data/ENTRATE.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.spese_fisse(id, id_mov, descrizione, mese) 
FROM './wallet/data/SPESE_FISSE.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.spese_mantenimento(id, id_mov, descrizione) 
FROM './wallet/data/SPESE_MANTENIMENTO.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.spese_varie(id, id_mov, id_tipo_spesa, descrizione) 
FROM './wallet/data/SPESE_VARIE.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.spese_viaggi(id, id_mov, viaggio, descrizione) 
FROM './wallet/data/SPESE_VIAGGI.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);

\copy public.stipendi(id, id_mov, ddl, mese, netto, totale, trattenute, rimborso_spese) 
FROM './wallet/data/STIPENDI.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ','
);


-- to update id field to last value in imported table
SELECT setval(pg_get_serial_sequence('MAP_TABELLE', 'id'), MAX(id)) FROM MAP_TABELLE;
SELECT setval(pg_get_serial_sequence('MAP_CONTI', 'id'), MAX(id)) FROM MAP_CONTI;
SELECT setval(pg_get_serial_sequence('MAP_ENTRATE', 'id'), MAX(id)) FROM MAP_ENTRATE;
SELECT setval(pg_get_serial_sequence('MAP_MOVIMENTI', 'id'), MAX(id)) FROM MAP_MOVIMENTI;
SELECT setval(pg_get_serial_sequence('MAP_SPESE_VARIE', 'id'), MAX(id)) FROM MAP_SPESE_VARIE;
SELECT setval(pg_get_serial_sequence('WALLET_USERS', 'id'), MAX(id)) FROM WALLET_USERS;
SELECT setval(pg_get_serial_sequence('MOVIMENTI', 'id'), MAX(id)) FROM MOVIMENTI;
SELECT setval(pg_get_serial_sequence('DEBITI_CREDITI', 'id'), MAX(id)) FROM DEBITI_CREDITI;
SELECT setval(pg_get_serial_sequence('ENTRATE', 'id'), MAX(id)) FROM ENTRATE;
SELECT setval(pg_get_serial_sequence('SPESE_FISSE', 'id'), MAX(id)) FROM SPESE_FISSE;
SELECT setval(pg_get_serial_sequence('SPESE_MANTENIMENTO', 'id'), MAX(id)) FROM SPESE_MANTENIMENTO;
SELECT setval(pg_get_serial_sequence('SPESE_VIAGGI', 'id'), MAX(id)) FROM SPESE_VIAGGI;
SELECT setval(pg_get_serial_sequence('SPESE_VARIE', 'id'), MAX(id)) FROM SPESE_VARIE;
SELECT setval(pg_get_serial_sequence('STIPENDI', 'id'), MAX(id)) FROM STIPENDI;