#!/bin/bash

if [[ ${PWD} == "${WALLET_}" ]]; then
    unset PGPASSWORD
fi

source ../config/wallet.env
source ../config/database.env

#fail
_SCRIPT_STATUS=0

DIR_NAME="$(date +%d%m%Y)"
DATA_FOLDER="${WALLET_DIR}/export/${DIR_NAME}"
TMP_CSV_DATA="${WALLET_CSV_FOLDER}/_${DIR_NAME}"

sudo -u ${USER} mkdir -p ${DATA_FOLDER}

# make tmp folder to share with user postgres
sudo -u ${MAIN_USER_DB} mkdir -p ${TMP_CSV_DATA}
# sudo -u ${MAIN_USER_DB} chmod 777 ${TMP_CSV_DATA}
sudo -u ${MAIN_USER_DB} chown postgres:postgres ${TMP_CSV_DATA}

export PGPASSWORD="${DB_ADMIN_PWD}"

# psql --port="${DB_PORT}" \
# 		--username="${DB_ADMIN}" \
# 		--dbname="${DB_NAME}" \
# 		--file="${WALLET_DIR}/sql/scripts/pgSQL/procedures/EXPORT_DATA.sql" \
# 		--no-password

# echo ${WALLET_CSV_FOLDER}
sudo -u ${MAIN_USER_DB} psql \
    --port "${DB_PORT}" \
		--dbname "${DB_NAME}"           \
    --command "CALL export_data('${WALLET_CSV_FOLDER}');"

if [ $? -ne 0 ]; then
	echo "Errore durante export csv da db ${DB_NAME}"
  _SCRIPT_STATUS=1
else
  echo "Export completato con successo"
fi

# if the script is run on the same process unset the password
if [[ "$0" == "${SHELL}" ]]; then
    unset PGPASSWORD
fi

echo ${WALLET_CSV_FOLDER}
echo ${DATA_FOLDER}

# sudo -u ${USER} mv ${WALLET_CSV_FOLDER}/*.csv ${DATA_FOLDER}/

# sudo -u ${USER} chmod -R 744 ${DATA_FOLDER}/*.csv
# sudo -u ${USER} chown ${USER}:${USER} ${DATA_FOLDER}/*.csv

exit ${_SCRIPT_STATUS}