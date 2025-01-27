CREATE DATABASE wallet;
\connect wallet;

BEGIN;

	CREATE SCHEMA w_map;
	CREATE SCHEMA w_data;

	-- for dates in format (GG/MM/AA)
	ALTER DATABASE wallet SET DateStyle = 'SQL, DMY';

	-- so the prefixes w_data/w_map are not necessary
	ALTER DATABASE wallet SET SEARCH_PATH TO w_data, w_map;

	CREATE TABLE w_map.MAP_TABELLE(
		ID serial primary key,
		NOME text NOT NULL,
		DESCRIZIONE text NOT NULL);

	CREATE TABLE w_map.MAP_CONTI(
		ID serial primary key,
		TIPO text NOT NULL,
		DESCRIZIONE text NOT NULL);

	CREATE TABLE w_map.MAP_ENTRATE(
		ID serial primary key,
		DESCRIZIONE text NOT NULL);

	CREATE TABLE w_map.MAP_MOVIMENTI(
		ID serial primary key,
		ID_TABLE int references w_map.MAP_TABELLE(ID),
		DESCRIZIONE text NOT NULL,
		STORED_PROCEDURE text NOT NULL,
		VIEW text NOT NULL);

	CREATE TABLE w_map.MAP_SPESE_VARIE(
		ID serial primary key,
		DESCRIZIONE text NOT NULL);

	CREATE TABLE w_data.MOVIMENTI(
		ID serial primary key,
		ID_TIPO_MOV int references w_map.MAP_MOVIMENTI(ID),
		ID_CONTO int references w_map.MAP_CONTI(ID),
		DATA_INS timestamp default CURRENT_TIMESTAMP,
		DATA_MOV date default CURRENT_DATE,
		DARE_AVERE boolean default true,
		IMPORTO real NOT NULL check (IMPORTO > 0),
		NOTE text default '');

	CREATE TABLE w_data.DEBITI_CREDITI(
		ID serial primary key,
		ID_MOV int references w_data.MOVIMENTI(ID),
		DEB_CRED boolean,
		ORIGINE text NOT NULL,
		DESCRIZIONE text NOT NULL,
		SALDATO boolean default false,
		ID_MOV_SALDO text default '',
		DATA_SALDO date default NULL);

	CREATE TABLE w_data.ENTRATE(
		ID serial primary key,
		ID_MOV int references w_data.MOVIMENTI(ID),
		ID_TIPO_ENTRATA int references w_map.MAP_ENTRATE(ID),
		DESCRIZIONE text NOT NULL);

	CREATE TABLE w_data.SPESE_FISSE(
		ID serial primary key,
		ID_MOV int references w_data.MOVIMENTI(ID),
		MESE int NOT NULL check (MESE between 1 and 12),
		DESCRIZIONE text NOT NULL);

	CREATE TABLE w_data.SPESE_MANTENIMENTO(
		ID serial primary key,
		ID_MOV int references w_data.MOVIMENTI(ID),
		DESCRIZIONE text NOT NULL);

	CREATE TABLE w_data.SPESE_VARIE(
		ID serial primary key,
		ID_MOV int references w_data.MOVIMENTI(ID),
		ID_TIPO_SPESA int references w_map.MAP_SPESE_VARIE(ID),
		DESCRIZIONE text NOT NULL);

	CREATE TABLE w_data.SPESE_VIAGGI(
		ID serial primary key,
		ID_MOV int references w_data.MOVIMENTI(ID),
		VIAGGIO text NOT NULL,
		DESCRIZIONE text NOT NULL);

	CREATE TABLE w_data.STIPENDI(
		ID serial primary key,
		ID_MOV int references w_data.MOVIMENTI(ID),
		DDL text NOT NULL,
		MESE int NOT NULL check (MESE between 1 and 12),
		LORDO real default 0 check (LORDO >= 0),
		TRATTENUTE real default 0 check (TRATTENUTE >= 0),
		RIMBORSO_SPESE real default 0 check (RIMBORSO_SPESE >= 0));

	-- to generate the sequence of INSERTs for every record of the table use this command:
	-- SELECT string_agg(
	-- 		'INSERT INTO MAP_TABLE (<LIST_FIELDS>) VALUES (' || FIELD1 || ', ' || FIELD2 || ', ''' || FIELD_STR || ''' [...] );',
	-- 		E'\n'
	-- ) AS insert_statements
	-- FROM MAP_TABLE;

	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (1, 'MOVIMENTI', 'Tabella principale che contiente il movimento generico');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (2, 'SPESE_VARIE', 'Tabella contenente spese di vario tipo');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (3, 'SPESE_FISSE', 'Tabella contenente spese fisse mensili');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (4, 'SPESE_LAVORO', 'Tabella contenente spese legate al lavoro');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (5, 'STIPENDI', 'Tabella contenente informazione sugli stipendi percepiti');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (6, 'DEBITI_CREDITI', 'Tabella che gestisce i prestiti');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (7, 'MAP_SPESE_VARIE', 'Tabella che mappa i tipi di spese variabili');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (8, 'MAP_PAGAMENTI', 'Tabella che mappa il modo in cui è stato fatto il movimento');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (9, 'UTENTI', 'Tabella che mappa gli utenti che hanno accesso al DB');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (11, 'ENTRATE', 'Tabella che memorizza le entrate diverse dagli stipendi');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (12, 'MAP_MOVIMENTI', 'Tabella che mappa i tipi generici di spese/entrate');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (13, 'MAP_TABELLE', 'Tabella che mappa tutte le altre tabelle');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (14, 'MAP_ENTRATE', 'Tabella che mappa i tipi di entrate');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (15, 'SPESE_MANTENIMENTO', 'Tabella contenente le spese per il mantenimeno ad Amsterdam');
	INSERT INTO w_map.MAP_TABELLE (ID, NOME, DESCRIZIONE) VALUES (16, 'SPESE_VIAGGI', 'Tabella contenente le spese fatte per ciascun viaggio');

	INSERT INTO w_map.MAP_CONTI (ID, TIPO, DESCRIZIONE) VALUES (1, 'Contante', 'Contante');
	INSERT INTO w_map.MAP_CONTI (ID, TIPO, DESCRIZIONE) VALUES (2, 'Carta', 'Unicredit');
	INSERT INTO w_map.MAP_CONTI (ID, TIPO, DESCRIZIONE) VALUES (4, 'Virtuale', 'Satispay');
	INSERT INTO w_map.MAP_CONTI (ID, TIPO, DESCRIZIONE) VALUES (6, 'Virtuale', 'Paypal');
	INSERT INTO w_map.MAP_CONTI (ID, TIPO, DESCRIZIONE) VALUES (7, 'Carta', 'Revolut');
	INSERT INTO w_map.MAP_CONTI (ID, TIPO, DESCRIZIONE) VALUES (8, 'Carta', 'ABN AMRO');

	INSERT INTO w_map.MAP_ENTRATE (ID, DESCRIZIONE) VALUES (1, 'Ristorazione');
	INSERT INTO w_map.MAP_ENTRATE (ID, DESCRIZIONE) VALUES (2, 'Vendite online');
	INSERT INTO w_map.MAP_ENTRATE (ID, DESCRIZIONE) VALUES (3, 'Soldi regalati');
	INSERT INTO w_map.MAP_ENTRATE (ID, DESCRIZIONE) VALUES (4, 'Varie');

	INSERT INTO w_map.MAP_MOVIMENTI (ID, ID_TABLE, DESCRIZIONE, STORED_PROCEDURE, VIEW) VALUES (1, 2, 'Spesa Varia', 'INSERISCI_SPESA_VARIA', 'V_SPESE_VARIE');
	INSERT INTO w_map.MAP_MOVIMENTI (ID, ID_TABLE, DESCRIZIONE, STORED_PROCEDURE, VIEW) VALUES (2, 3, 'Spesa Fissa', 'INSERISCI_SPESA_FISSA', 'V_SPESE_FISSE');
	INSERT INTO w_map.MAP_MOVIMENTI (ID, ID_TABLE, DESCRIZIONE, STORED_PROCEDURE, VIEW) VALUES (3, 5, 'Stipendio', 'INSERISCI_STIPENDIO', 'V_STIPENDI');
	INSERT INTO w_map.MAP_MOVIMENTI (ID, ID_TABLE, DESCRIZIONE, STORED_PROCEDURE, VIEW) VALUES (4, 11, 'Entrata', 'INSERISCI_ENTRATA', 'V_ENTRATE');
	INSERT INTO w_map.MAP_MOVIMENTI (ID, ID_TABLE, DESCRIZIONE, STORED_PROCEDURE, VIEW) VALUES (5, 6, 'Debito - Credito', 'INSERISCI_DEBITO_CREDITO', 'V_DEBITI_CREDITI_APERTI');
	INSERT INTO w_map.MAP_MOVIMENTI (ID, ID_TABLE, DESCRIZIONE, STORED_PROCEDURE, VIEW) VALUES (6, 6, 'Saldo Debito - Credito', 'SALDA_DEBITO_CREDITO', 'V_DEBITI_CREDITI_APERTI');
	INSERT INTO w_map.MAP_MOVIMENTI (ID, ID_TABLE, DESCRIZIONE, STORED_PROCEDURE, VIEW) VALUES (7, 15, 'Spesa di Mantenimento', 'INSERISCI_SPESA_MANTENIMENTO', 'V_SPESE_MANTENIMENTO');
	INSERT INTO w_map.MAP_MOVIMENTI (ID, ID_TABLE, DESCRIZIONE, STORED_PROCEDURE, VIEW) VALUES (8, 16, 'Spesa di Viaggio', 'INSERISCI_SPESA_VIAGGIO', 'V_SPESE_VIAGGI');

	INSERT INTO w_map.MAP_SPESE_VARIE (ID, DESCRIZIONE) VALUES (1, 'Cibo');
	INSERT INTO w_map.MAP_SPESE_VARIE (ID, DESCRIZIONE) VALUES (2, 'Acquisti online');
	INSERT INTO w_map.MAP_SPESE_VARIE (ID, DESCRIZIONE) VALUES (3, 'Vestiti');
	INSERT INTO w_map.MAP_SPESE_VARIE (ID, DESCRIZIONE) VALUES (5, 'Varie');
	INSERT INTO w_map.MAP_SPESE_VARIE (ID, DESCRIZIONE) VALUES (6, 'Droghe');

COMMIT;
