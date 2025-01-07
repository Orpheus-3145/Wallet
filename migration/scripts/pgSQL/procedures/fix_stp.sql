DO $$
DECLARE
	id_row int;
    note_row text;
BEGIN

	SET search_path TO w_data, w_map;

    CREATE TABLE w_data.STIPENDI_with_note(
                ID int,
                ID_MOV int,
                DDL text,
                MESE int,
                TOTALE real,
                NETTO real,
                TRATTENUTE real,
                RIMBORSO_SPESE real,
                NOTE text);

    COPY STIPENDI_with_note
    FROM '/var/lib/pgsql/Wallet/migration/data/import/STIPENDI_tmp.csv'
    WITH (
            FORMAT csv,
            HEADER true,
            DELIMITER '|'
    );

    FOR id_row, note_row IN SELECT ID_MOV, NOTE from STIPENDI_with_note
    LOOP    

        UPDATE MOVIMENTI SET NOTE=note_row WHERE ID=id_row;

	END LOOP;

    DROP TABLE STIPENDI_with_note;

END $$;