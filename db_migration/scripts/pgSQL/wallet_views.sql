create view V_DEBITI_CREDITI_APERTI as
select
	TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')								as DATA,
	ROUND(mv.IMPORTO::numeric, 2)											as IMPORTO,
	case when mv.DARE_AVERE = true then 'Debito' else 'Credito' end	as DEBITO_CREDITO,
	dc.ORIGINE														as ORIGINE,
	dc.DESCRIZIONE													as DESCRIZIONE,
	mv.NOTE															as NOTE,
	mv.ID															as ID
from MOVIMENTI mv
inner join DEBITI_CREDITI dc on
	mv.ID = ID_MOV
where SALDATO = false;


create view V_ENTRATE as
select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')				as DATA,
	ROUND(IMPORTO::numeric, 2)			as IMPORTO,
	COALESCE(mnt.DESCRIZIONE, '')	as TIPO,
	ent.DESCRIZIONE				as DESCRIZIONE,
	COALESCE(mv.NOTE, '')			as NOTE,
	mv.ID						as ID
from MOVIMENTI mv
inner join ENTRATE ent on
	ent.ID_MOV = mv.id
left join MAP_ENTRATE mnt on
	mnt.id = ent.ID_TIPO_ENTRATA;


create view V_SPESE_FISSE as
select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')				as DATA,
	ROUND(IMPORTO::numeric, 2)			as IMPORTO,
	sf.DESCRIZIONE				as DESCRIZIONE,
	mc.DESCRIZIONE				as PAGAMENTO,
	COALESCE(mv.NOTE, '')			as NOTE,
	mv.ID						as ID
from MOVIMENTI mv
inner join SPESE_FISSE sf on
	sf.ID_MOV = mv.id
inner join MAP_conti mc on
	mv.ID_CONTO = mc.id;


create view V_SPESE_MANTENIMENTO as
select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')				as DATA,
	ROUND(IMPORTO::numeric, 2)									as IMPORTO,
	sm.DESCRIZIONE										as DESCRIZIONE,
	COALESCE(mv.NOTE, '')									as NOTE,
	mv.ID												as ID
from MOVIMENTI mv
inner join SPESE_MANTENIMENTO sm on
	sm.ID_MOV = mv.id;


create view V_SPESE_VARIE as
select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')	as DATA,
	ROUND(IMPORTO::numeric, 2)						as IMPORTO,
	msv.DESCRIZIONE							as TIPO,
	sv.DESCRIZIONE							as DESCRIZIONE,
	COALESCE(mv.NOTE, '')						as NOTE,
	mv.ID									as ID
from MOVIMENTI mv
inner join SPESE_VARIE sv on
	sv.ID_MOV = mv.id
inner join MAP_SPESE_VARIE msv on
	msv.id = sv.ID_TIPO_SPESA;


create view V_SPESE_VIAGGI as
select TO_CHAR(mv.DATA_MOV, 'dd/MM/yyyy')				as DATA,
	ROUND(IMPORTO::numeric, 2)									as IMPORTO,
	sv.VIAGGIO										as VIAGGIO,
	sv.DESCRIZIONE										as DESCRIZIONE,
	COALESCE(mv.NOTE, '')									as NOTE,
	mv.ID												as ID
from MOVIMENTI mv
inner join SPESE_VIAGGI sv on
	sv.ID_MOV = mv.id;


create view V_STIPENDI as
select
	ROUND(stp.NETTO::numeric, 2)				as NETTO,
	ROUND(stp.TRATTENUTE::numeric, 2)		as TRATTENUTE,
	ROUND(stp.RIMBORSO_SPESE::numeric, 2)	as R_SPESE,
	MESE,
	stp.DDL							as DDL,
	mv.ID							as ID
from MOVIMENTI mv
inner join STIPENDI stp on
	stp.ID_MOV = mv.id;

