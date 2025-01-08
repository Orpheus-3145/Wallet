use Wallet


create table [dbo].[MAP_RUOLI_TABELLE](
	[ID] [int] identity(1,1) primary key,
	[DESCRIZIONE] [varchar](max) not null
)
GO


create table [dbo].[MAP_TABELLE](
	[ID] [int] identity(1,1) primary key,
	[ID_RUOLO] int not null,
	[NOME] [varchar](max) not null,
	[DESCRIZIONE] [varchar](max) not null,

	foreign key (ID_RUOLO) references MAP_RUOLI_TABELLE(ID)
)
GO


create table [dbo].[MAP_CONTI](
	[ID] [int] identity(1,1) primary key,
	[TIPO] [varchar](max) not null,
	[DESCRIZIONE] [varchar](max) not null
)
GO


create table [dbo].[MAP_ENTRATE](
	[ID] [int] identity(1,1) primary key,
	[DESCRIZIONE] [varchar](max) not null,
)
GO


create table [dbo].[MAP_MOVIMENTI](
	[ID] [int] identity(1,1) primary key,
	[ID_TABLE] [int] not null,
	[DESCRIZIONE] [varchar](max) not null,
	[STORED_PROCEDURE] [varchar](max) not null,
	[VIEW] [varchar](max) not null,

	foreign key (ID_TABLE) references MAP_TABELLE(ID)
)
GO


create table [dbo].[MAP_SPESE_VARIE](
	[ID] [int] identity(1,1) primary key,
	[DESCRIZIONE] [varchar](max) not null
)
GO


create table [dbo].[QLIK_USERS](
	[ID] [int] identity(1,1) primary key,
	--[ID_RUOLO] [int] not null,  non necessario probabilmente [altrimenti la tabella MAP_RUOLI va creata]
	[RUOLO] [varchar](10) default '',    -- o rimuovere il campo oppure usare sopra
	[USERNAME] [varchar](max) not null,
	[PASSWORD] [varchar](max) not null,
	[NOTE] [varchar](max) default ''
	
	--foreign key (ID_RUOLO) references MAP_RUOLI(ID)
)
GO


create table [dbo].[WALLET_USERS](
	[ID] [int] identity(1,1) primary key,
	--[ID_RUOLO] [int] not null,  non necessario probabilmente [altrimenti la tabella MAP_RUOLI va creata]
	[USERNAME] [varchar](max) not null,
	[PASSWORD] [varchar](max) not null,
	[NOTE] [varchar](max) default ''
	
	--foreign key (ID_RUOLO) references MAP_RUOLI(ID)
)
GO


create table [dbo].[MOVIMENTI](
	[ID] [int] identity(1,1) primary key,
	[ID_TIPO_MOV] [int] not null,
	[ID_CONTO] [int] not null,
	[DATA_INS] [datetime] default GETDATE(),
	[DATA_MOV] [date] default GETDATE(),
	[DARE_AVERE] [bit] default 0,
	[IMPORTO] [real] not null CHECK (IMPORTO > 0),
	[NOTE] [varchar](max) default ''
	
	foreign key (ID_TIPO_MOV) references MAP_MOVIMENTI(ID),
	foreign key (ID_CONTO) references MAP_CONTI(ID)
)
GO


create table [dbo].[DEBITI_CREDITI](
	[ID] [int] identity(1,1) primary key,
	[ID_MOV] [int] not null,
	[DEB_CRED] [bit] default 0,
	[ORIGINE] [varchar](max) not null,
	[DESCRIZIONE] [varchar](max) not null,
	[SALDATO] [bit] default 0,
	[ID_MOV_SALDO] [varchar](max) default '',
	[DATA_SALDO] [date] default NULL
	
	foreign key (ID_MOV) references MOVIMENTI(ID),
)
GO


create table [dbo].[ENTRATE](
	[ID] [int] identity(1,1) primary key,
	[ID_MOV] [int] not null,
	[ID_TIPO_ENTRATA] [int] not null,
	[DESCRIZIONE] [varchar](max) not null,

	foreign key (ID_MOV) references MOVIMENTI(ID),
	foreign key (ID_TIPO_ENTRATA) references MAP_ENTRATE(ID),
)
GO


create table [dbo].[SPESE_FISSE](
	[ID] [int] identity(1,1) primary key,
	[ID_MOV] [int] not null,
	[MESE] [int] default MONTH(GETDATE()),
	[DESCRIZIONE] [varchar](max) not null
	
	foreign key (ID_MOV) references MOVIMENTI(ID),
)
GO


create table [dbo].[SPESE_MANTENIMENTO](
	[ID] [int] identity(1,1) primary key,
	[ID_MOV] [int] not null,
	[DESCRIZIONE] [varchar](max) not null
	
	foreign key (ID_MOV) references MOVIMENTI(ID),
)
GO


create table [dbo].[SPESE_VARIE](
	[ID] [int] identity(1,1) primary key,
	[ID_MOV] [int] not null,
	[ID_TIPO_SPESA] [int] not null,
	[DESCRIZIONE] [varchar](max) not null

	foreign key (ID_MOV) references MOVIMENTI(ID),
	foreign key (ID_TIPO_SPESA) references MAP_SPESE_VARIE(ID),
)
GO


create table [dbo].[SPESE_VIAGGI](
	[ID] [int] identity(1,1) primary key,
	[ID_MOV] [int] not null,
	[VIAGGIO] [varchar](max) not null,
	[DESCRIZIONE] [varchar](max) not null
	
	foreign key (ID_MOV) references MOVIMENTI(ID),
)
GO


create table [dbo].[STIPENDI](
	[ID] [int] identity(1,1) primary key,
	[ID_MOV] [int] not null,
	[DDL] [varchar](max) not null,
	[MESE] [int] not null,
	[NETTO] [real] not null CHECK ([NETTO] > 0),
	[TOTALE] [real] default 0 CHECK ([TOTALE] >= 0),
	[TRATTENUTE] [real] default 0 CHECK ([TRATTENUTE] >= 0),
	[RIMBORSO_SPESE] [real] default 0 CHECK ([RIMBORSO_SPESE] >= 0)
	
	foreign key (ID_MOV) references MOVIMENTI(ID),
)
GO
