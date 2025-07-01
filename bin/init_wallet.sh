#!/bin/bash

source ../config/wallet.env

SCRIPT_SQL="${PATH_SQL_SCRIPTS}/create_tables.sql"
psql --port="${DB_PORT}" \
	--username="${USER}" \
	--dbname="postgres" \
	--file="${SCRIPT_SQL}"

SCRIPT_SQL="${PATH_SQL_SCRIPTS}/create_views.sql"
psql --port="${DB_PORT}" \
	--username="${USER}" \
	--dbname="${DB_NAME}" \
	--file="${SCRIPT_SQL}" \
	--no-password

SCRIPT_SQL="${PATH_SQL_SCRIPTS}/create_users.sql"
psql --port="${DB_PORT}" \
	--username="${USER}" \
	--dbname="${DB_NAME}" \
	--file="${SCRIPT_SQL}" \
	--set=admin_name="${DB_ADMIN}" \
	--set=admin_pwd="${DB_ADMIN_PWD}" \
	--set=user_name="${DB_USER}" \
	--set=user_pwd="${DB_USER_PWD}"

export PGPASSWORD="${DB_ADMIN_PWD}"
PROCS_SCRIPTS_DIR="${PATH_SQL_SCRIPTS}/procedures"

if [ ! -d "${PROCS_SCRIPTS_DIR}" ]; then
  echo "error: missing directory ${PROCS_SCRIPTS_DIR}"
	
	# if the script is run on the same process unset the password
	if [ $? -ne 0 ]; then
		unset PGPASSWORD
	fi

	exit 1
fi

for sql_file in "${PROCS_SCRIPTS_DIR}"/*.sql; do

  psql --port="${DB_PORT}" \
		--username="${DB_ADMIN}" \
		--dbname="${DB_NAME}" \
		--file="${sql_file}" \
		--no-password

  if [ $? -ne 0 ]; then
		echo "error while running ${sql_file}. Interrupt"
	
		# if the script is run on the same process unset the password
		if [ $? -ne 0 ]; then
			unset PGPASSWORD
		fi

		exit 1
  fi
done

# if the script is run on the same process unset the password
if [ $? -ne 0 ]; then
	unset PGPASSWORD
fi

# creating table that stores csv exports
sudo mkdir -p ${WALLET_CSV_FOLDER_PG}
sudo chmod 777 ${WALLET_CSV_FOLDER_PG}
sudo chown -R postgres:postgres ${WALLET_CSV_FOLDER_PG}
