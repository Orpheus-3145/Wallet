#!/bin/bash

source "${WALLET_DIR}/config/wallet.env"
source "${WALLET_DIR}/config/database.env"

DATA_FOLDER="${DB_NAME}-csv-$(date +%d%m%Y_%H%M%S)"
TMP_CSV_DATA="${WALLET_CSV_FOLDER}/${DATA_FOLDER}"
# make tmp folder to give later ownership to #USER
sudo -u ${MAIN_USER_DB} mkdir -p ${TMP_CSV_DATA}

export PGPASSWORD="${DB_ADMIN_PWD}"

sudo -u ${MAIN_USER_DB} psql \
    --port "${DB_PORT}" \
		--dbname "${DB_NAME}" \
    --command "CALL export_data('${TMP_CSV_DATA}');"

if [[ $? != "0" ]]; then
	echo "Errore durante export csv da db ${DB_NAME}"

  # if the script is run on the same process unset the password
  if [[ "$0" == "${SHELL}" ]]; then
    unset PGPASSWORD
  fi

  exit 1
fi

echo "Export completato con successo"

# if the script is run on the same process unset the password
if [[ "$0" == "${SHELL}" ]]; then
    unset PGPASSWORD
fi

# move tmp folder of user postgres and change ownership
sudo mv ${TMP_CSV_DATA} "${WALLET_DIR}/export"
sudo chown -R ${USER}:${USER} "${WALLET_DIR}/export/${DATA_FOLDER}"

echo "Spostato la cartella con csv e cambiato le ownership"
