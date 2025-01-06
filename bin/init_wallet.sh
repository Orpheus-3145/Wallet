#!/bin/bash

source ../settings/.pgsql_env

SCRIPT_SQL="${PATH_SQL_SCRIPTS}/create_tables.sql"
psql --port="${DB_PORT}" \
     --username="${DB_ADMIN}" \
     --file="${SCRIPT_SQL}"

SCRIPT_SQL="${PATH_SQL_SCRIPTS}/create_user.sql"
psql --port="${DB_PORT}" \
     --username="${DB_ADMIN}" \
     --dbname="${DB_NAME}" \
     --file="${SCRIPT_SQL}" \
     --set=user_db="${DB_USER}" \
     --set=pwd_db="${DB_USER_PWD}"

SCRIPT_SQL="${PATH_SQL_SCRIPTS}/create_views.sql"
psql --port="${DB_PORT}" \
     --username="${DB_ADMIN}" \
     --dbname="${DB_NAME}" \
     --file="${SCRIPT_SQL}" \

PROCS_SCRIPTS_DIR="${PATH_SQL_SCRIPTS}/procedures"

if [ ! -d "${PROCS_SCRIPTS_DIR}" ]; then
  echo "error: missing directory ${PROCS_SCRIPTS_DIR}"
  exit 1
fi

for sql_file in "${PROCS_SCRIPTS_DIR}"/*.sql; do

  psql --port="${DB_PORT}" \
       --username="${DB_ADMIN}" \
       --dbname="${DB_NAME}" \
       --file="${sql_file}"

  if [ $? -ne 0 ]; then
    echo "error while running ${sql_file}. Interrupt"
    exit 1
  fi
done

# import csv data
psql --port="${DB_PORT}" \
     --username="${DB_ADMIN}" \
     --dbname="${DB_NAME}" \
     --command="CALL w_data.import_data('${PATH_SQL_DATA_CSV/}/');"