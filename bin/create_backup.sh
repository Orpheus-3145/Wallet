#!/bin/bash
source ../config/wallet.env

BACKUP_FILE="${PATH_BACKUP_DIR}/${DB_NAME}-$(date +%Y%m%d_%H%M%S).tar"

mkdir -p "${PATH_BACKUP_DIR}"

export PGPASSWORD="${DB_USER_PWD}"

pg_dump --port "${DB_PORT}"             \
		--username "${DB_USER_NAME}"    \
		--dbname "${DB_NAME}"           \
		--format t       				\
		--file "${BACKUP_FILE}"			\
		--create --verbose

if [ $? -ne 0 ]; then
	echo "Errore durante il backup del database: ${DB_NAME}"
	exit 1
fi

echo "Backup completato con successo: ${BACKUP_FILE}"
