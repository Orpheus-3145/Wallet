CREATE OR REPLACE FUNCTION prepare_backup(db_name TEXT, backup_path TEXT)
RETURNS TEXT AS $$
DECLARE
    backup_file TEXT;
BEGIN
    -- Generare il nome del file di backup con timestamp
    backup_file := backup_path || '/' || db_name || '-' || TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDD_HH24MISS') || '.sql';

    -- Inserire nel log l'operazione
    -- INSERT INTO backup_log (db_name, backup_file)
    -- VALUES (db_name, backup_file);

    -- Restituire il comando pg_dump da eseguire esternamente
    RETURN FORMAT('pg_dump -U postgres -F c -d %I -f %L', db_name, backup_file);
END;
$$ LANGUAGE plpgsql;