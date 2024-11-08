use [Wallet]


create procedure [dbo].[BK_DATABASE]
@bk_path nvarchar(max),
@db_to_backup nvarchar(30)
as
begin
	backup database @db_to_backup
	to disk = @bk_path
	with no_log
end



create procedure [dbo].[INSERISCI_DEB_CRED]
	@data_mov DATE,						-- data del movimento
	@importo REAL,						-- importo
	@id_conto INT,						-- id pagamento
	@deb_cred BIT,						-- debito o credito
	@descrizione NVARCHAR(MAX),			-- descrizione
	@origine NVARCHAR(MAX),				-- origine
	@note NVARCHAR(MAX) = ''			-- note
as
begin
	-- checks
	declare @err_msg nvarchar(256) = ''
	if @importo < 0
	begin;
		set @err_msg = 'Importo [' + CONVERT(NVARCHAR(10), @importo) + '] negativo';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_CONTI where id=@id_conto) = 0
	begin
		set @err_msg = 'Id conto [' + CONVERT(NVARCHAR(10), @id_conto) + '] non esistente';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_MOVIMENTI where DESCRIZIONE='Debito - Credito') = 0
	begin
		set @err_msg = 'Errore interno, movimento [Debito - Credito] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @id_tipo_mov INT = (select ID from MAP_MOVIMENTI where DESCRIZIONE = 'Debito - Credito')
	declare @dare_avere INT = (select case when @deb_cred = 0 then 1 else 0 end)
	begin transaction

	insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @importo, @dare_avere, @id_tipo_mov, @id_conto, @note)
	
	declare @id_mov_main VARCHAR(MAX) = (select TOP 1 CAST(ID as VARCHAR(MAX)) from MOVIMENTI order by ID desc)		-- recupero l'ID del movimento principale appena inserito per riferirmi ad esso successivamente
	
	insert into DEBITI_CREDITI (ID_MOV, DEB_CRED, DESCRIZIONE, ORIGINE, SALDATO, ID_MOV_SALDO, DATA_SALDO) values (@id_mov_main, @deb_cred, @descrizione, @origine, 0, NULL, NULL)

	commit transaction
end



create procedure [dbo].[INSERISCI_ENTRATA]
	@data_mov DATE,	-- data del movimento
	@importo REAL,						-- importo
	@id_conto INT,						-- id pagamento
	@id_tipo_entrata INT,				-- provenienza
	@descrizione NVARCHAR(MAX),			-- descrizione
	@note NVARCHAR(MAX) = ''			-- note
as
begin
	-- checks
	declare @err_msg nvarchar(256) = ''
	if @importo < 0
	begin;
		set @err_msg = 'Importo [' + CONVERT(NVARCHAR(10), @importo) + '] negativo';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_CONTI where id=@id_conto) = 0
	begin
		set @err_msg = 'Id conto [' + CONVERT(NVARCHAR(10), @id_conto) + '] non esistente';
		throw 55555, @err_msg, 1;
	end
	
	if (select count(*) from MAP_ENTRATE where id=@id_tipo_entrata) = 0
	begin
		set @err_msg = 'Id entrata [' + CONVERT(NVARCHAR(10), @id_tipo_entrata) + '] non esistente';
		throw 55555, @err_msg, 1;
	end
	
	if (select count(*) from MAP_MOVIMENTI where DESCRIZIONE='Entrata') = 0
	begin
		set @err_msg = 'Errore interno, movimento [Entrata] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @id_tipo_mov INT = (select ID from MAP_MOVIMENTI where DESCRIZIONE = 'Entrata')			-- id del movimento
	begin transaction

	insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @importo, 1, @id_tipo_mov, @id_conto, @note)
	
	declare @id_mov_main INT = (select TOP 1 CAST(ID as VARCHAR(MAX)) from MOVIMENTI order by ID desc)		-- recupero l'ID del movimento principale appena inserito per riferirmi ad esso successivamente
	
	insert into ENTRATE(ID_MOV, ID_TIPO_ENTRATA, DESCRIZIONE) values (@id_mov_main, @id_tipo_entrata, @descrizione)

	commit transaction
end



create procedure [dbo].[INSERISCI_S_FISSA]
	@data_mov DATE,				-- data del movimento
	@importo REAL,				-- importo
	@id_conto INT,				-- id pagamento
	@descrizione NVARCHAR(MAX),	-- descrizione
	@note NVARCHAR(MAX) = ''	-- note
as
begin
	-- set NOCOUNT on added to prevent extra result sets from
	-- interfering with SELECT statements.
	set NOCOUNT on;
	
	-- checks
	declare @err_msg nvarchar(256) = ''
	if @importo < 0
	begin;
		set @err_msg = 'Importo [' + CONVERT(NVARCHAR(10), @importo) + '] negativo';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_CONTI where id=@id_conto) = 0
	begin
		set @err_msg = 'Id conto [' + CONVERT(NVARCHAR(10), @id_conto) + '] non esistente';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_MOVIMENTI where DESCRIZIONE='Spesa Fissa') = 0
	begin
		set @err_msg = 'Errore interno, movimento [Spesa Fissa] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @id_tipo_mov INT = (select ID from MAP_MOVIMENTI where DESCRIZIONE = 'Spesa Fissa')		-- id del movimento
	declare @mese INT = 0																			-- mese (successivo)
	if MONTH(@data_mov) = 12
	begin
		set @mese = 1
	end
	else
	begin
		set @mese = MONTH(@data_mov) + 1
	end
	begin transaction

	insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @importo, 0, @id_tipo_mov, @id_conto, @note)
	
	declare @id_mov_main INT = (select TOP 1 CAST(ID as VARCHAR(MAX)) from MOVIMENTI order by ID desc)		-- recupero l'ID del movimento principale appena inserito per riferirmi ad esso successivamente
	
	insert into SPESE_FISSE(ID_MOV, DESCRIZIONE, MESE) values (@id_mov_main, @descrizione, @mese)

	commit transaction
end



create procedure [dbo].[INSERISCI_S_MANTENIMENTO]
	@data_mov DATE,				-- data del movimento
	@importo REAL,				-- importo
	@id_conto INT,				-- id pagamento
	@descrizione NVARCHAR(MAX),	-- descrizione
	@note NVARCHAR(MAX) = ''	-- note
as
begin
	-- set NOCOUNT on added to prevent extra result sets from
	-- interfering with SELECT statements.
	set NOCOUNT on;
	
	-- checks
	declare @err_msg nvarchar(256) = ''
	if @importo < 0
	begin;
		set @err_msg = 'Importo [' + CONVERT(NVARCHAR(10), @importo) + '] negativo';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_CONTI where id=@id_conto) = 0
	begin
		set @err_msg = 'Id conto [' + CONVERT(NVARCHAR(10), @id_conto) + '] non esistente';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_MOVIMENTI where DESCRIZIONE='Spesa di Mantenimento') = 0
	begin
		set @err_msg = 'Errore interno, movimento [Spesa di Mantenimento] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @id_tipo_mov INT = (select ID from MAP_MOVIMENTI where DESCRIZIONE = 'Spesa di Mantenimento')	-- id del movimento
	begin transaction

	insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @importo, 0, @id_tipo_mov, @id_conto, @note)
	
	declare @id_mov_main INT = (select TOP 1 CAST(ID as VARCHAR(MAX)) from MOVIMENTI order by ID desc)		-- recupero l'ID del movimento principale appena inserito per riferirmi ad esso successivamente
	
	insert into SPESE_MANTENIMENTO(ID_MOV, DESCRIZIONE) values (@id_mov_main, @descrizione)

	commit transaction
end



create procedure [dbo].[INSERISCI_S_VARIA]
	@data_mov DATE,					-- data del movimento
	@importo REAL,						-- importo
	@id_conto INT,					-- id pagamento
	@id_tipo_s_varia INT,				-- id tipo spesa varia
	@descrizione NVARCHAR(MAX),			-- descrizione
	@note NVARCHAR(MAX) = ''			-- note
as
begin
	-- set NOCOUNT on added to prevent extra result sets from
	-- interfering with SELECT statements.
	set NOCOUNT on;
	
	-- checks
	declare @err_msg nvarchar(256) = ''
	if @importo < 0
	begin;
		set @err_msg = 'Importo [' + CONVERT(NVARCHAR(10), @importo) + '] negativo';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_CONTI where id=@id_conto) = 0
	begin
		set @err_msg = 'Id conto [' + CONVERT(NVARCHAR(10), @id_conto) + '] non esistente';
		throw 55555, @err_msg, 1;
	end
	
	if (select count(*) from MAP_SPESE_VARIE where id=@id_tipo_s_varia) = 0
	begin
		set @err_msg = 'Id spesa varia [' + CONVERT(NVARCHAR(10), @id_tipo_s_varia) + '] non esistente';
		throw 55555, @err_msg, 1;
	end
	
	if (select count(*) from MAP_MOVIMENTI where DESCRIZIONE='Spesa Varia') = 0
	begin
		set @err_msg = 'Errore interno, movimento [Spesa Varia] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @id_tipo_mov INT = (select ID from MAP_MOVIMENTI where DESCRIZIONE = 'Spesa Varia')		-- id del movimento
	begin transaction

	insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @importo, 0, @id_tipo_mov, @id_conto, @note)
	
	declare @id_mov_main INT = (select TOP 1 CAST(ID as VARCHAR(MAX)) from MOVIMENTI order by ID desc)		-- recupero l'ID del movimento principale appena inserito per riferirmi ad esso successivamente
	
	insert into SPESE_VARIE (ID_MOV, ID_TIPO_SPESA, DESCRIZIONE) values (@id_mov_main, @id_tipo_s_varia, @descrizione)

	commit transaction
end



create procedure [dbo].[INSERISCI_S_VIAGGIO]
	@data_mov DATE,					-- data del movimento
	@importo REAL,						-- importo
	@id_conto INT,					-- id pagamento
	@viaggio NVARCHAR(MAX),				-- viaggio
	@descrizione NVARCHAR(MAX),			-- descrizione
	@note NVARCHAR(MAX) = ''			-- note
as
begin
	-- set NOCOUNT on added to prevent extra result sets from
	-- interfering with SELECT statements.
	set NOCOUNT on;
	
	-- checks
	declare @err_msg nvarchar(256) = ''
	if @importo < 0
	begin;
		set @err_msg = 'Importo [' + CONVERT(NVARCHAR(10), @importo) + '] negativo';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_CONTI where id=@id_conto) = 0
	begin
		set @err_msg = 'Id conto [' + CONVERT(NVARCHAR(10), @id_conto) + '] non esistente';
		throw 55555, @err_msg, 1;
	end
	
	if (select count(*) from MAP_MOVIMENTI where DESCRIZIONE='Spesa di Viaggio') = 0
	begin
		set @err_msg = 'Errore interno, movimento [Spesa di Viaggio] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @id_tipo_mov INT = (select ID from MAP_MOVIMENTI where DESCRIZIONE = 'Spesa di Viaggio')	-- id del movimento
	begin transaction
	
	insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @importo, 0, @id_tipo_mov, @id_conto, @note)
	
	declare @id_mov_main INT = (select TOP 1 CAST(ID as VARCHAR(MAX)) from MOVIMENTI order by ID desc)		-- recupero l'ID del movimento principale appena inserito per riferirmi ad esso successivamente
	
	insert into SPESE_VIAGGI(ID_MOV, VIAGGIO, DESCRIZIONE) values (@id_mov_main, @viaggio, @descrizione)

	commit transaction
end



create procedure [dbo].[INSERISCI_STIPENDIO]
	@data_mov DATE,					-- data del movimento
	@importo REAL,						 
	@netto REAL = 0,					-- se importo <> allora ci sono trattenutte e/o r. spese				 
	@rimborso_spese REAL = 0,				 
	@id_conto INT,						-- id pagamento
	@ddl NVARCHAR(MAX),					-- datore di lavoro
	@note NVARCHAR(MAX) = ''			-- note
as
begin
	-- set NOCOUNT on added to prevent extra result sets from
	-- interfering with SELECT statements.
	set NOCOUNT on;
	
	-- checks
	declare @err_msg nvarchar(256) = ''
	if @importo < 0
	begin;
		set @err_msg = 'Importo [' + CONVERT(NVARCHAR(10), @importo) + '] negativo';
		throw 55555, @err_msg, 1;
	end
	
	if @netto < 0
	begin;
		set @err_msg = 'Netto [' + CONVERT(NVARCHAR(10), @netto) + '] negativo';
		throw 55555, @err_msg, 1;
	end
	else if @netto > @importo
	begin;
		set @err_msg = 'Netto [' + CONVERT(NVARCHAR(10), @netto) + '] maggiore dell''importo [' + CONVERT(NVARCHAR(10), @importo) + ']';
		throw 55555, @err_msg, 1;
	end

	if @rimborso_spese < 0
	begin;
		set @err_msg = 'R. spese [' + CONVERT(NVARCHAR(10), @rimborso_spese) + '] negativo';
		throw 55555, @err_msg, 1;
	end
	else if @rimborso_spese > @importo
	begin;
		set @err_msg = 'Rimborso spese [' + CONVERT(NVARCHAR(10), @rimborso_spese) + '] maggiore dell''importo ' + CONVERT(NVARCHAR(10), @importo) + ']';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_CONTI where id=@id_conto) = 0
	begin
		set @err_msg = 'Id conto [' + CONVERT(NVARCHAR(10), @id_conto) + '] non esistente';
		throw 55555, @err_msg, 1;
	end
	
	if (select count(*) from MAP_MOVIMENTI where DESCRIZIONE='Stipendio') = 0
	begin
		set @err_msg = 'Errore interno, movimento [Stipendio] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @id_tipo_mov INT = (select ID from MAP_MOVIMENTI where DESCRIZIONE = 'Stipendio')		-- id del movimento
	declare @mese INT = 0																			-- mese (precedente)
	if MONTH(@data_mov) = 1
	begin
		set @mese = 12
	end
	else
	begin
		set @mese = MONTH(@data_mov) - 1
	end
	if @netto = 0
	begin
		set @netto = @importo
	end
	declare @trattenute REAL = 0
	if @importo > (@netto + @rimborso_spese)
	begin
		set @trattenute = @importo - @netto - @rimborso_spese
	end
	begin transaction

	insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @netto, 1, @id_tipo_mov, @id_conto, @note)
	
	declare @id_mov_main INT = (select TOP 1 CAST(ID as VARCHAR(MAX)) from MOVIMENTI order by ID desc)		-- recupero l'ID del movimento principale appena inserito per riferirmi ad esso successivamente
	
	insert into STIPendI(ID_MOV, DDL, MESE, TOTALE, NETTO, TRATTENUTE, RIMBORSO_SPESE) values (@id_mov_main, @ddl, @mese, @importo, @netto, @trattenute, @rimborso_spese)
	
	commit transaction
end



create procedure [dbo].[READ_MOVEMENTS]
@id_tipo_mov INT,
@n_records INT
as
begin
	-- set NOCOUNT on added to prevent extra result sets from
	-- interfering with SELECT statements.
	set NOCOUNT on;
	
	-- checks
	declare @err_msg nvarchar(256) = ''
	if (select count(*) from MAP_MOVIMENTI where id = @id_tipo_mov) = 0
	begin
		set @err_msg = 'Movimento id [' + @id_tipo_mov + '] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	if @n_records <= 0
	begin
		set @err_msg = 'Numero di record da leggere negativo [' + CONVERT(NVARCHAR(10), @n_records) + ']';
		throw 55555, @err_msg, 1;
	end

	declare @view_name NVARCHAR(MAX) = 'V_' + (select TABLE_NAME from MAP_MOVIMENTI where id = @id_tipo_mov)
	if (select count(*) from sys.views where name = @view_name) = 0
	begin
		set @err_msg = 'Vista [' + @view_name + '] non esistente';
		throw 55555, @err_msg, 1;
	end

	declare @sql_statement NVARCHAR(MAX) = 'SELECT TOP (__n_rows__) v.* FROM __view_name__ v INNER JOIN MOVIMENTI mv on mv.id = v.id ORDER BY mv.DATA_MOV DESC'
	set @sql_statement = REPLACE(@sql_statement, '__n_rows__', @n_records)
	set @sql_statement = REPLACE(@sql_statement, '__view_name__', @view_name)
	EXEC sp_executesql @sql_statement
end



create procedure [dbo].[REMOVE_MOVEMENT]
	@id_mov_to_drop INT
as
begin
	-- set NOCOUNT on added to prevent extra result sets from
	-- interfering with SELECT statements.
	set NOCOUNT on;
	
	-- checks
	declare @err_msg nvarchar(256) = ''
	if (select count(*) from MOVIMENTI where id = @id_mov_to_drop) = 0
	begin
		set @err_msg = 'Movimento id [' + @id_mov_to_drop + '] non trovato in MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @id_tipo_mov INT = (select ID_TIPO_MOV from MOVIMENTI where ID = @id_mov_to_drop)
	if (select count(*) from MAP_MOVIMENTI where id = @id_tipo_mov) = 0
	begin
		set @err_msg = 'Tipo movimento id [' + @id_tipo_mov + '] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @table_name NVARCHAR(MAX) = (select TABLE_NAME from MAP_MOVIMENTI where id = @id_tipo_mov)
	declare @sql_statement NVARCHAR(MAX) = 'DELETE __table_name__ WHERE ID_MOV = __id_mov_to_drop__'
	set @sql_statement = REPLACE(@sql_statement, '__table_name__', @table_name)
	set @sql_statement = REPLACE(@sql_statement, '__id_mov_to_drop__', @id_mov_to_drop)

	DELETE MOVIMENTI WHERE ID = @id_mov_to_drop
	EXEC sp_executesql @sql_statement
end



create procedure [dbo].[SALDA_DEB_CRED]
	@id_saldo_deb_cred NVARCHAR(MAX),	-- lista di ID da saldare
	@data_mov DATE,					-- data del movimento
	@importo REAL = 0.0,				-- importo in input, default 0
	@id_conto INT,					-- id pagamento
	@note NVARCHAR(MAX) = ''			-- note
as
begin
	-- set NOCOUNT on added to prevent extra result sets from
	-- interfering with SELECT statements.
	set NOCOUNT on;

	-- checks
	declare @err_msg nvarchar(256) = ''
	if @id_saldo_deb_cred = ''
	begin;
		throw 55555, 'Invalid IDs, usage: id1, id2, ...', 1;
	end

	begin try		-- check if ids are formatted as integers comma separated, then creates a column of the ids to iterate later
		declare @temp_id_table TABLE (ID int)
		insert into @temp_id_table select ID from MOVIMENTI where ID in (select value from STRING_SPLIT(@id_saldo_deb_cred, ',')) order by IMPORTO;
	end try
	begin catch
		set @err_msg = 'Invalid IDs [' + @id_saldo_deb_cred + '] usage: id1, id2, ...';
		throw 55555, @err_msg, 1;
	end catch
		
	if (select count(distinct dc.ORIGINE) from DEBITI_CREDITI dc inner join @temp_id_table tmp on tmp.ID = dc.ID_MOV) > 1		-- check se ho selezionato deb/cred provenienti dalla stessa origine
	begin;
		throw 55555, 'Selezionati deb/cred da diversa origine', 1;
	end
	
	if @importo <> 0.0 and (select count(distinct dc.DEB_CRED) from DEBITI_CREDITI dc inner join @temp_id_table tmp on tmp.ID = dc.ID_MOV) > 1		-- se é stata passato manualmente un importo, allora il saldo devo riguardare solo tutti debiti o tuti crediti, non misto
	begin;
		throw 55555, 'Selezionati debiti e crediti in contemporanea da saldare in modo parziale', 1;
	end
	
	if @importo < 0
	begin;
		set @err_msg = 'Importo: ' + CONVERT(NVARCHAR(10), @importo) + ' negativo';
		throw 55555, @err_msg, 1;
	end

	if (select count(*) from MAP_CONTI where id=@id_conto) = 0
	begin
		set @err_msg = 'Id conto [' + CONVERT(NVARCHAR(10), @id_conto) + '] non esistente';
		throw 55555, @err_msg, 1;
	end
	
	if (select count(*) from MAP_MOVIMENTI where DESCRIZIONE='Saldo Debito - Credito') = 0
	begin
		set @err_msg = 'Errore interno, movimento [Saldo Debito - Credito] non trovato in MAP_MOVIMENTI';
		throw 55555, @err_msg, 1;
	end

	declare @tot_importo REAL = (select cast(sum(case when DARE_AVERE = 1 then importo * -1 else importo end) as decimal(9, 2))			-- importo totale da saldare dei deb/cred selezionati
							from DEBITI_CREDITI dc 
							inner join MOVIMENTI mv on 
								mv.ID = dc.ID_MOV 
							inner join @temp_id_table tmp on 
								tmp.ID = dc.ID_MOV)
	declare @origine VARCHAR(MAX) = (select distinct ORIGINE								-- origine comune dei deb/cred selzionati
							from DEBITI_CREDITI dc
							inner join @temp_id_table tmp on 
								tmp.ID = dc.ID_MOV)
	declare @dare_avere INT = (select case when @tot_importo > 0 then 1 else 0 end)	-- dare-avere del futuro movimento (se importo é negativo spesa, positivo entrata)
	declare @id_tipo_mov INT = (select ID from MAP_MOVIMENTI where DESCRIZIONE = 'Saldo Debito - Credito')	-- id movimento
	if @tot_importo < 0
	begin
		set @tot_importo = @tot_importo * -1
	end
	declare @curr_importo INT = 0								-- progressivo dei deb/cred saldati
	declare @current_id INT = 0									-- index per iterare sui vari ID
	declare id_cursor CURSOR for select ID from @temp_id_table	-- cursor per iterare sui vari ID
	declare @id_mov_main VARCHAR(MAX) = ''						-- id del movimento principale
	declare @id_mov_opt INT = 0									-- id del movimento opzionale (ovvero se @diff <> 0)
	declare @diff REAL = 0										-- diff importo input - importo tot sa saldare
	
	if @importo > @tot_importo
	begin
		set @diff = @importo - @tot_importo
	end
	else if @importo <> 0.0 and @importo < @tot_importo
	begin
		set @tot_importo = @importo
	end
	
	begin transaction

	insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @tot_importo, @dare_avere, @id_tipo_mov, @id_conto, @note + ' - saldo deb/cred di id ' + @id_saldo_deb_cred)
	set @id_mov_main = (select TOP 1 CAST(ID as VARCHAR(MAX)) from MOVIMENTI order by ID desc)		-- recupero l'ID del movimento principale appena inserito per riferirmi ad esso successivamente

	open id_cursor;
	fetch next from id_cursor INTO @current_id;
	while @@FETCH_STATUS = 0			-- per ogni ID presente nella lista degli id, aggiorno il relativo record della tab DEBITI_CREDITI
	begin
		if @importo = 0.0		-- no importo in input, saldo pulito
		begin
			update DEBITI_CREDITI set SALDATO = 1, ID_MOV_SALDO = ISNULL(ID_MOV_SALDO, '') + @id_mov_main, DATA_SALDO = @data_mov where ID_MOV = @current_id
		end
		else						-- con importo in input, c'é un parziale
		begin
			set @curr_importo = (select IMPORTO from MOVIMENTI where ID = @current_id)
			if @importo >= @curr_importo
			begin
				update DEBITI_CREDITI set SALDATO = 1, ID_MOV_SALDO = ISNULL(ID_MOV_SALDO, '') + @id_mov_main, DATA_SALDO = @data_mov where ID_MOV = @current_id
				set @importo = @importo - @curr_importo
			end
			else			-- in questo caso non riesco a saldare lo specifico deb/cred, modifico l'importo di quello che riesco a saldare ed esco dal loop
			begin
				update DEBITI_CREDITI set ID_MOV_SALDO = ISNULL(ID_MOV_SALDO, '') + @id_mov_main + ', ' where ID_MOV = @current_id
				update MOVIMENTI set IMPORTO = @importo where ID = @current_id
				break
			end
		end
		fetch next from id_cursor INTO @current_id;
	end;
	close id_cursor;
	deallocate id_cursor;

	if @diff > 0		-- se diff > 0 allora viene creato un altro debito/credito oltre al saldo, che rappresenta il credito/debito che tiene conto dell'avanzo, che a sua volta dovrà essere saldato
	begin
		if @dare_avere = 0
		begin
			insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @diff, 1, 9, @id_conto, NULL)
			set @id_mov_opt = (select TOP 1 ID from MOVIMENTI order by ID desc)
			insert into DEBITI_CREDITI (ID_MOV, DEB_CRED, DESCRIZIONE, ORIGINE, SALDATO, ID_MOV_SALDO, DATA_SALDO) values (@id_mov_opt, 1, 'Eccesso del saldo id ' + @id_mov_main, @origine, 0, NULL, NULL)
		end
		else
		begin
			insert into MOVIMENTI (DATA_MOV, DATA_INS, IMPORTO, DARE_AVERE, ID_TIPO_MOV, ID_CONTO, NOTE) values (@data_mov, GETDATE(), @diff, 0, 9, @id_conto, NULL)
			set @id_mov_opt = (select TOP 1 ID from MOVIMENTI order by ID desc)
			insert into DEBITI_CREDITI (ID_MOV, DEB_CRED, DESCRIZIONE, ORIGINE, SALDATO, ID_MOV_SALDO, DATA_SALDO) values (@id_mov_opt, 0, 'Eccesso del saldo id ' + @id_mov_main, @origine, 0, NULL, NULL)
		end
	end

	commit transaction
end


create procedure [dbo].[TURN_INTO_MOVEMENT] 
	@id_record INT	-- per deb/crediti mai salvati che diventano entrate/spese
as
BEGIN
	-- set NOCOUNT on added to prevent extra result sets from
	-- interfering with SELECT statements.
	set NOCOUNT on;

	-- checks
	declare @err_msg nvarchar(256) = ''
	if (select count(*) from MOVIMENTI where id = @id_record) = 0
	begin
		set @err_msg = 'Movimento id [' + @id_record + '] non trovato in MOVIMENTI';
		throw 55555, @err_msg, 1;
	end
	
	if (select count(*) from DEBITI_CREDITI where ID_MOV = @id_record) = 0
	begin
		set @err_msg = 'Debito-credito riferito ad id_mov [' + @id_record + '] non trovato in DEBITI_CREDITI';
		throw 55555, @err_msg, 1;
	end

	declare @dare_avere INT = (select DARE_AVERE from MOVIMENTI where ID = @id_record)
	declare @desc_deb_cred VARCHAR(MAX) = (select DESCRIZIONE from DEBITI_CREDITI where ID_MOV = @id_record)
	declare @src_deb_cred VARCHAR(MAX) = (select ORIGINE from DEBITI_CREDITI where ID_MOV = @id_record)
	begin transaction

	delete DEBITI_CREDITI where id_mov = @id_record and SALDATO = 0
	if @dare_avere = 1		-- il debito diventa un'entrata
	begin
		update MOVIMENTI set ID_TIPO_MOV = 4 where ID = @id_record
		insert into ENTRATE values (@id_record, 4, 'Debito diventato entrata, ' + @src_deb_cred + ': ' + @desc_deb_cred)
	end
	else							-- il credito diventa una spesa
	begin
		update MOVIMENTI set ID_TIPO_MOV = 1 where id = @id_record
		insert into SPESE_VARIE values (@id_record, 5, 'Credito diventato spesa, ' + @src_deb_cred + ': ' + @desc_deb_cred)
	end

	commit transaction
END
