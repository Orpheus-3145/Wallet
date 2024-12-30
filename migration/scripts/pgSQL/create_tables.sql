-- \set map_schema :'w_map'
-- \set data_schema :'w_data'

CREATE DATABASE wallet;
\c wallet;

DO $$
DECLARE
	map_schema_name text := :map_schema;
	data_schema_name text := :data_schema;
BEGIN

	-- schema for mapped values
	EXECUTE format(
		'CREATE SCHEMA %s'
		, map_schema_name);

	-- schema to store data
	EXECUTE format(
		'CREATE SCHEMA %s'
		, data_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.MAP_TABELLE(
			ID serial primary key,
			NOME text NOT NULL,
			DESCRIZIONE text NOT NULL
		)', map_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.MAP_CONTI(
			ID serial primary key,
			TIPO text NOT NULL,
			DESCRIZIONE text NOT NULL
		)', map_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.MAP_ENTRATE(
			ID serial primary key,
			DESCRIZIONE text NOT NULL
		)', map_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.MAP_MOVIMENTI(
			ID serial primary key,
			ID_TABLE int references %s.MAP_TABELLE(ID),
			DESCRIZIONE text NOT NULL,
			STORED_PROCEDURE text NOT NULL
		)', map_schema_name, map_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.MAP_SPESE_VARIE(
			ID serial primary key,
			DESCRIZIONE text NOT NULL
		)', map_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.MOVIMENTI(
			ID serial primary key,
			ID_TIPO_MOV int references %s.MAP_MOVIMENTI(ID),
			ID_CONTO int references %s.MAP_CONTI(ID),
			DATA_INS timestamp default CURRENT_TIMESTAMP,
			DATA_MOV date default CURRENT_DATE,
			DARE_AVERE boolean default true,
			IMPORTO real NOT NULL check (IMPORTO > 0),
			NOTE text default ''''
		)', data_schema_name, map_schema_name, map_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.DEBITI_CREDITI(
			ID serial primary key,
			ID_MOV int references %s.MOVIMENTI(ID),
			DEB_CRED boolean,
			ORIGINE text NOT NULL,
			DESCRIZIONE text NOT NULL,
			SALDATO boolean default false,
			ID_MOV_SALDO text default '''',
			DATA_SALDO date default NULL
		)', data_schema_name, data_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.ENTRATE(
			ID serial primary key,
			ID_MOV int references %s.MOVIMENTI(ID),
			ID_TIPO_ENTRATA int references %s.MAP_ENTRATE(ID),
			DESCRIZIONE text NOT NULL
		)', data_schema_name, data_schema_name, map_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.SPESE_FISSE(
			ID serial primary key,
			ID_MOV int references %s.MOVIMENTI(ID),
			MESE int NOT NULL check (MESE between 1 and 12),
			DESCRIZIONE text NOT NULL
		)', data_schema_name, data_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.SPESE_MANTENIMENTO(
			ID serial primary key,
			ID_MOV int references %s.MOVIMENTI(ID),
			DESCRIZIONE text NOT NULL
		)', data_schema_name, data_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.SPESE_VARIE(
			ID serial primary key,
			ID_MOV int references %s.MOVIMENTI(ID),
			ID_TIPO_SPESA int references %s.MAP_SPESE_VARIE(ID),
			DESCRIZIONE text NOT NULL
		)', data_schema_name, data_schema_name, map_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.SPESE_VIAGGI(
			ID serial primary key,
			ID_MOV int references %s.MOVIMENTI(ID),
			VIAGGIO text NOT NULL,
			DESCRIZIONE text NOT NULL
		)', data_schema_name, data_schema_name);

	EXECUTE format(
		'CREATE TABLE %s.STIPENDI(
			ID serial primary key,
			ID_MOV int references %s.MOVIMENTI(ID),
			DDL text NOT NULL,
			MESE int NOT NULL check (MESE between 1 and 12),
			NETTO real NOT NULL check (NETTO > 0),
			TOTALE real default 0 check (TOTALE >= 0),
			TRATTENUTE real default 0 check (TRATTENUTE >= 0),
			RIMBORSO_SPESE real default 0 check (RIMBORSO_SPESE >= 0)
		)', data_schema_name, data_schema_name);
	
END $$;
