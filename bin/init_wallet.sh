#!/bin/bash

source ../.pgsql_env

psql -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "create_tables.sql"
psql -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "create_user.sql"
psql -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "create_views.sql"

SQL_DIR="./procedures"

if [ ! -d "$SQL_DIR" ]; then
  echo "error: missing directory $SQL_DIR"
  exit 1
fi

# Esportare la password per l'autenticazione automatica
export PGPASSWORD=$DB_PASSWORD

for sql_file in "$SQL_DIR"/*.sql; do

  psql -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file"

  if [ $? -ne 0 ]; then
    echo "error while running $sql_file. Interrupt"
    exit 1
  fi
done

# unset PGPASSWORD
