--TUTTE LE TAB MENO MOVIMENTI
-- creo backup
SELECT * INTO WALLET_USERS_BK FROM UTENTI
DROP TABLE UTENTI

-- creo nuova colonna con ID identity(1,1) come PK
CREATE TABLE WALLET_USERS(
	[ID] INT IDENTITY(1,1) PRIMARY KEY,
	USERNAME VARCHAR(20) NOT NULL,
	PASSWORD VARCHAR(100) NOT NULL,
	RUOLO VARCHAR(10) NOT NULL)

--inserisco i valori corretti nella nuova tabella modificando le due colonne id e id_mov
SET IDENTITY_INSERT QLIK_USERS OFF
SET IDENTITY_INSERT WALLET_USERS ON

insert into WALLET_USERS (
      [ID]
      ,[USERNAME]
      ,[PASSWORD]
      ,[RUOLO]
	  )
select convert(int, right(id, len(id) - 4)) as ID
      ,[USERNAME]
      ,[PASSWORD]
      ,[RUOLO]
from WALLET_USERS_BK

-- rimuovo la cartella di backup
drop table WALLET_USERS_BK
--SELECT * FROM MOVIMENTI
--select * from MOVIMENTI_bk
