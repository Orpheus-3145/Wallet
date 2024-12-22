DO $$
DECLARE
	data_schema_name text := 'w_data';
	map_schema_name text := 'w_map';
BEGIN

	EXECUTE format( $query$
		create view %s.V_DEBITI_CREDITI_APERTI as
		select
			TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')								as DATA,
			ROUND(mv.IMPORTO::numeric, 2)											as IMPORTO,
			case when mv.DARE_AVERE = true then 'Debito' else 'Credito' end	as DEBITO_CREDITO,
			dc.ORIGINE														as ORIGINE,
			dc.DESCRIZIONE													as DESCRIZIONE,
			mv.NOTE															as NOTE,
			mv.ID															as ID
		from %s.MOVIMENTI mv
		inner join %s.DEBITI_CREDITI dc on
			mv.ID = ID_MOV
		where SALDATO = false
	$query$ , data_schema_name, data_schema_name, data_schema_name);

	EXECUTE format( $query$
		create view %s.V_ENTRATE as
		select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')				as DATA,
			ROUND(IMPORTO::numeric, 2)			as IMPORTO,
			COALESCE(mnt.DESCRIZIONE, '')	as TIPO,
			ent.DESCRIZIONE				as DESCRIZIONE,
			COALESCE(mv.NOTE, '')			as NOTE,
			mv.ID						as ID
		from %s.MOVIMENTI mv
		inner join %s.ENTRATE ent on
			ent.ID_MOV = mv.id
		left join %s.MAP_ENTRATE mnt on
			mnt.id = ent.ID_TIPO_ENTRATA
	$query$ , data_schema_name, data_schema_name, data_schema_name, map_schema_name);

	EXECUTE format( $query$
		create view %s.V_SPESE_FISSE as
		select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')				as DATA,
			ROUND(IMPORTO::numeric, 2)			as IMPORTO,
			sf.DESCRIZIONE				as DESCRIZIONE,
			mc.DESCRIZIONE				as PAGAMENTO,
			COALESCE(mv.NOTE, '')			as NOTE,
			mv.ID						as ID
		from %s.MOVIMENTI mv
		inner join %s.SPESE_FISSE sf on
			sf.ID_MOV = mv.id
		inner join %s.MAP_conti mc on
			mv.ID_CONTO = mc.id
	$query$ , data_schema_name, data_schema_name, data_schema_name, map_schema_name);

	EXECUTE format( $query$
		create view %s.V_SPESE_MANTENIMENTO as
		select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')				as DATA,
			ROUND(IMPORTO::numeric, 2)									as IMPORTO,
			sm.DESCRIZIONE										as DESCRIZIONE,
			COALESCE(mv.NOTE, '')									as NOTE,
			mv.ID												as ID
		from %s.MOVIMENTI mv
		inner join %s.SPESE_MANTENIMENTO sm on
			sm.ID_MOV = mv.id
	$query$ , data_schema_name, data_schema_name, data_schema_name);

	EXECUTE format( $query$
		create view %s.V_SPESE_VARIE as
		select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')	as DATA,
			ROUND(IMPORTO::numeric, 2)						as IMPORTO,
			msv.DESCRIZIONE							as TIPO,
			sv.DESCRIZIONE							as DESCRIZIONE,
			COALESCE(mv.NOTE, '')						as NOTE,
			mv.ID									as ID
		from %s.MOVIMENTI mv
		inner join %s.SPESE_VARIE sv on
			sv.ID_MOV = mv.id
		inner join %s.MAP_SPESE_VARIE msv on
			msv.id = sv.ID_TIPO_SPESA
	$query$ , data_schema_name, data_schema_name, data_schema_name, map_schema_name);

	EXECUTE format( $query$
		create view %s.V_SPESE_VIAGGI as
		select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')				as DATA,
			ROUND(IMPORTO::numeric, 2)									as IMPORTO,
			sv.VIAGGIO										as VIAGGIO,
			sv.DESCRIZIONE										as DESCRIZIONE,
			COALESCE(mv.NOTE, '')									as NOTE,
			mv.ID												as ID
		from %s.MOVIMENTI mv
		inner join %s.SPESE_VIAGGI sv on
			sv.ID_MOV = mv.id
	$query$ , data_schema_name, data_schema_name, data_schema_name);

	EXECUTE format( $query$
		create view %s.V_STIPENDI as
		select
			ROUND(stp.NETTO::numeric, 2)				as NETTO,
			ROUND(stp.TRATTENUTE::numeric, 2)		as TRATTENUTE,
			ROUND(stp.RIMBORSO_SPESE::numeric, 2)	as R_SPESE,
			MESE,
			stp.DDL							as DDL,
			mv.ID							as ID
		from %s.MOVIMENTI mv
		inner join %s.STIPENDI stp on
			stp.ID_MOV = mv.id
	$query$ , data_schema_name, data_schema_name, data_schema_name);

END $$;