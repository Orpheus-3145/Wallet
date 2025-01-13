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
	NETTO real NOT NULL check (NETTO > 0),
	TOTALE real default 0 check (TOTALE >= 0),
	TRATTENUTE real default 0 check (TRATTENUTE >= 0),
	RIMBORSO_SPESE real default 0 check (RIMBORSO_SPESE >= 0));

COMMIT;
