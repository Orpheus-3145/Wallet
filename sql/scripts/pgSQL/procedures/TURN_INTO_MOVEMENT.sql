CREATE OR REPLACE PROCEDURE w_data.TURN_INTO_MOVEMENT(
    id_record int
)
LANGUAGE plpgsql AS $$
DECLARE
    -- procedure variables
    dare_avere boolean DEFAULT FALSE;
    date_deb_cred text DEFAULT '';
    desc_deb_cred text DEFAULT '';
    src_deb_cred text DEFAULT '';
    new_description text DEFAULT '';

BEGIN
    SELECT CAST(DATA_MOV AS text) INTO STRICT date_deb_cred
        FROM w_data.MOVIMENTI mv
        WHERE ID = id_record;

    SELECT mv.DARE_AVERE INTO STRICT dare_avere
        FROM w_data.MOVIMENTI mv
        WHERE ID = id_record;

    SELECT DESCRIZIONE INTO STRICT desc_deb_cred
        FROM w_data.DEBITI_CREDITI
        WHERE ID_MOV = id_record AND SALDATO = FALSE;

    SELECT ORIGINE INTO STRICT src_deb_cred
        FROM w_data.DEBITI_CREDITI
        WHERE ID_MOV = id_record AND SALDATO = FALSE;

	DELETE FROM w_data.DEBITI_CREDITI WHERE ID_MOV = id_record;

    IF DARE_AVERE = FALSE THEN
        new_description = format('Credito verso %s [data: %s] diventato spesa, vecchie note: %s', src_deb_cred, date_deb_cred, desc_deb_cred);
        
        -- ID_TIPO_MOV is hardcoded with 1 ('Spesa Varia')
        UPDATE w_data.MOVIMENTI SET ID_TIPO_MOV = 1 WHERE id = id_record;
        
		INSERT INTO w_data.SPESE_VARIE(ID_MOV, ID_TIPO_SPESA, DESCRIZIONE)
            VALUES (id_record, 5, new_description);
    ELSE
        new_description = format('Debito verso %s [data: %s] diventato entrata, vecchie note: %s', src_deb_cred, date_deb_cred, desc_deb_cred);

        -- ID_TIPO_MOV is hardcoded with 4 ('Entrata')
        UPDATE w_data.MOVIMENTI SET ID_TIPO_MOV = 4 WHERE ID = id_record;

		INSERT INTO w_data.ENTRATE(ID_MOV, ID_TIPO_ENTRATA, DESCRIZIONE)
            VALUES (id_record, 4, new_description);
    END IF;

EXCEPTION
	WHEN NO_DATA_FOUND THEN
		RAISE EXCEPTION 'Unable to retrive movement data [DARE_AVERE, DESCRIZIONE, ORIGINE] from id movement: %', id_record USING HINT = 'Internal error';

END;
$$;