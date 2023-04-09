-- creo vista per spese variabili
create view V_SPESE_VARIE AS
select format(mv.DATA_MOV, 'dd/MM/yyyy')	as DATA,			
	round(IMPORTO, 2)						as IMPORTO,
	msv.DESCRIZIONE							as TIPO,					
	sv.DESCRIZIONE							as DESCRIZIONE,		
	mp.DESCRIZIONE							as 'TIPO PAGAMENTO', 
	isnull(mv.NOTE, '')							as NOTE,
	mv.ID									as ID
FROM MOVIMENTI mv
inner join SPESE_VARIE sv on		
	sv.ID_MOV = mv.id				
inner join MAP_PAGAMENTI mp on
	mv.ID_PAG = mp.id
inner join MAP_SPESE_VARIE msv on
	msv.id = sv.ID_TIPO_SPESA

-- creo vista spese fisse
create view V_SPESE_FISSE AS
select format(mv.DATA_MOV, 'dd/MM/yyyy')		as DATA,			
	round(IMPORTO, 2)							as IMPORTO,				
	sf.DESCRIZIONE								as DESCRIZIONE,		
	mp.DESCRIZIONE								as 'TIPO PAGAMENTO', 
	isnull(mv.NOTE, '')							as NOTE,
	mv.ID										as ID
FROM MOVIMENTI mv
inner join SPESE_FISSE sf on		
	sf.ID_MOV = mv.id				
inner join MAP_PAGAMENTI mp on
	mv.ID_PAG = mp.id

-- creo vista spese lavoro
create view V_SPESE_LAVORO AS
select format(mv.DATA_MOV, 'dd/MM/yyyy')					as DATA,			
	round(IMPORTO, 2)										as IMPORTO,		
	sl.DESCRIZIONE											as DESCRIZIONE,		
	mp.DESCRIZIONE											as 'TIPO PAGAMENTO',
	case when sl.RIMBORSATO = 0 then 'Sì' else 'No' end		as RIMBORSATO,
	isnull(mv.NOTE, '')										as NOTE,
	mv.ID													as ID
FROM MOVIMENTI mv
inner join SPESE_LAVORO sl on		
	sl.ID_MOV = mv.id				
inner join MAP_PAGAMENTI mp on
	mv.ID_PAG = mp.id

-- creo vista entrate
create view V_ENTRATE AS
select format(mv.DATA_MOV, 'dd/MM/yyyy')	as DATA,			
	round(IMPORTO, 2)						as IMPORTO,				
	ent.ORIGINE								as ORIGINE,
	ent.DESCRIZIONE							as DESCRIZIONE,		
	mp.DESCRIZIONE							as 'TIPO PAGAMENTO',
	isnull(mv.NOTE, '')						as NOTE,
	mv.ID									as ID
FROM MOVIMENTI mv
inner join ENTRATE ent on		
	ent.ID_MOV = mv.id				
inner join MAP_PAGAMENTI mp on
	mv.ID_PAG = mp.id

-- creo vista stipendi
create view V_STIPENDI AS
select format(mv.DATA_MOV, 'dd/MM/yyyy')		as DATA,	
	round(stp.TOTALE_LORDO)						as LORDO,
	round(mv.IMPORTO)							as NETTO,					
	datename(month, mv.DATA_MOV) 				as MESE,
	mp.DESCRIZIONE								as 'TIPO PAGAMENTO',
	isnull(stp.NOTE, '')						as NOTE,
	mv.ID										as ID
FROM MOVIMENTI mv
inner join STIPENDI stp on		
	stp.ID_MOV = mv.id				
inner join MAP_PAGAMENTI mp on
	mv.ID_PAG = mp.id

	