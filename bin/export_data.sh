#!/bin/bash

cd ${WALLET_DIR}/export

source "../config/wallet.env"
source "../config/database.env"

CSV_DATA="${DB_NAME}-csv-$(date +%d%m%Y_%H%M%S)"
TMP_CSV_DATA="${WALLET_CSV_FOLDER_PG}/${CSV_DATA}"

# make tmp folder to give later ownership to #USER
sudo -u ${MAIN_USER_DB} mkdir -p ${TMP_CSV_DATA}

export PGPASSWORD="${DB_ADMIN_PWD}"

sudo -u ${MAIN_USER_DB} psql \
		--port "${DB_PORT}" \
		--dbname "${DB_NAME}" \
		--command "CALL export_data('${TMP_CSV_DATA}');"

if [[ $? != "0" ]]; then
	echo -e "Errore durante export csv da db ${DB_NAME}"

	# if the script is run on the same process unset the password
	if [[ "$0" == "${SHELL}" ]]; then
		unset PGPASSWORD
	fi

	exit 1
fi

echo -e "Export effettuato in ${WALLET_DIR}/export/${CSV_DATA}"

# if the script is run on the same process unset the password
if [[ "$0" == "${SHELL}" ]]; then
		unset PGPASSWORD
fi

# move tmp folder of user postgres and change ownership
sudo mv ${TMP_CSV_DATA} "${CSV_DATA}"
sudo chown -R ${USER}:${USER} "${CSV_DATA}"

echo -e "Spostato la cartella con csv e cambiato le ownership"

read -p "Salvare in zip file? (y/n): " ZIP_FILES

if [[ "${ZIP_FILES,,}" == "y" ]]; then
		read -p "Crittografare zip? (y/n): " ENCRYPT_ZIP

		if [[ "${ENCRYPT_ZIP,,}" == "y" ]]; then
			7z a -tzip -p${DB_USER_PWD} -mem=AES256 ${CSV_DATA}.zip ${CSV_DATA}
			echo -e "\nCreato ${CSV_DATA}.zip (criptato) in ${PWD}"
		else
			zip -r ${CSV_DATA}.zip ${CSV_DATA}
			echo -e "\nCreato ${CSV_DATA}.zip in ${PWD}"
		fi
fi

