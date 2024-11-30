#!/bin/bash

# Configurazione
PG_USER="nome_utente"       # Utente del database
PG_PASSWORD="password"      # Password dell'utente
PG_HOST="localhost"         # Host del database
PG_PORT="5432"              # Porta del database
PG_DBNAME="nome_database"   # Nome del database
BACKUP_DIR="/path/to/backup" # Directory dove salvare il backup
DATE=$(date +%Y%m%d_%H%M%S) # Timestamp per differenziare i backup
BACKUP_FILE="$BACKUP_DIR/$PG_DBNAME-$DATE.sql"

# Creare la directory di backup se non esiste
mkdir -p "$BACKUP_DIR"

# Comando di backup
export PGPASSWORD="$PG_PASSWORD" # Imposta la password
pg_dump -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -F c -d "$PG_DBNAME" -f "$BACKUP_FILE"

# Controlla se il backup è andato a buon fine
if [ $? -eq 0 ]; then
    echo "Backup completato con successo: $BACKUP_FILE"
else
    echo "Errore durante il backup del database: $PG_DBNAME"
    exit 1
fi
