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