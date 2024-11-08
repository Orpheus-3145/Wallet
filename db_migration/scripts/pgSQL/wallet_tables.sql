create table MAP_RUOLI_TABELLE(
	ID serial primary key,
	DESCRIZIONE text not NULL
)

create table MAP_TABELLE(
	ID serial primary key,
	ID_RUOLO int references MAP_RUOLI_TABELLE(ID),
	NOME text not NULL,
	DESCRIZIONE text not NULL,
)

create table MAP_CONTI(
	ID serial primary key,
	TIPO text not NULL,
	DESCRIZIONE text not NULL
)

create table MAP_ENTRATE(
	ID serial primary key,
	DESCRIZIONE text not NULL,
)

create table MAP_MOVIMENTI(
	ID serial primary key,
	ID_TABLE int references MAP_TABELLE(ID),
	--ID_SP int references MAP_SP(ID),   when there's gonna be a table MAP_SP references foreign key MAP_SP(ID), remove STORED_PROCEDURE column then
	DESCRIZIONE text not NULL,
	STORED_PROCEDURE text not NULL,
)

create table MAP_SPESE_VARIE(
	ID serial primary key,
	DESCRIZIONE text not NULL
)

create table QLIK_USERS(
	ID serial primary key,
	USERNAME text not NULL,
	PASSWORD text not NULL,
	NOTE text default ''
)

create table WALLET_USERS(
	ID serial primary key,
	USERNAME text not NULL,
	PASSWORD text not NULL,
	NOTE text default ''
)

create table MOVIMENTI(
	ID serial primary key,
	ID_TIPO_MOV int references MAP_MOVIMENTI(ID),
	ID_CONTO int references MAP_CONTI(ID),
	DATA_INS timestamp default CURRENT_TIMESTAMP(),
	DATA_MOV date default CURRENT_DATE,
	DARE_AVERE boolean default 0,
	IMPORTO real not NULL check (IMPORTO > 0),
	NOTE text default ''
)

create table DEBITI_CREDITI(
	ID serial primary key,
	ID_MOV int references MOVIMENTI(ID),
	DEB_CRED boolean default 0,
	ORIGINE text not NULL,
	DESCRIZIONE text not NULL,
	SALDATO boolean default 0,
	ID_MOV_SALDO text default '',
	DATA_SALDO date default NULL
)

create table ENTRATE(
	ID serial primary key,
	ID_MOV int references MOVIMENTI(ID),
	ID_TIPO_ENTRATA int references MAP_ENTRATE(ID),
	DESCRIZIONE text not NULL,
)

create table SPESE_FISSE(
	ID serial primary key,
	ID_MOV int references MOVIMENTI(ID),
	MESE int not NULL check (MESE between 1 and 12),
	DESCRIZIONE text not NULL
)

create table SPESE_MANTENIMENTO(
	ID serial primary key,
	ID_MOV int references MOVIMENTI(ID),
	DESCRIZIONE text not NULL
)

create table SPESE_VARIE(
	ID serial primary key,
	ID_MOV int references MOVIMENTI(ID),
	ID_TIPO_SPESA int references MAP_SPESE_VARIE(ID),
	DESCRIZIONE text not NULL
)

create table SPESE_VIAGGI(
	ID serial primary key,
	ID_MOV int references MOVIMENTI(ID),
	VIAGGIO text not NULL,
	DESCRIZIONE text not NULL
)

create table STIPENDI(
	ID serial primary key,
	ID_MOV int references MOVIMENTI(ID),
	DDL text not NULL,
	MESE int not NULL check (MESE between 1 and 12),
	NETTO real not NULL check (NETTO > 0),
	TOTALE real default 0 check (TOTALE >= 0),
	TRATTENUTE real default 0 check (TRATTENUTE >= 0),
	RIMBORSO_SPESE real default 0 check (RIMBORSO_SPESE >= 0)
)
