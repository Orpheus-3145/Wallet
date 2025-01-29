import psycopg2                         # info: https://www.psycopg.org/docs/usage.html
import subprocess
import os

from AppExceptions import *
import Tools                            # funzioni generiche di supporto


class Wallet:
	def __init__(self, logger=None):
		self._logger = logger
		self._seq_test_mov = os.getenv("WALLET_TEST_MOV_SEQUENCE", "scram-sha-256")

	def connect(self, host_db, port_db, db_name, user, password, auth_mode):
		try:
			self.connection = psycopg2.connect(
				dbname=db_name,
				user=user,
				password=password,
				# host=host_db,
				port=port_db,
				require_auth=auth_mode
			)
		except psycopg2.Error as err:
			if "password authentication failed" in str(err):
				raise WrongInputException(f"Wrong password for user {user}")
			else:
				raise SqlError(f"Login failed: {str(err)}")
		else:
			self.cursor = self.connection.cursor()
			self.connection.autocommit = False

	def disconnect_database(self):
		self.connection.close()

	def backup_database(self):
		try:
			subprocess.run(["bash", os.getenv("PATH_BACKUP_SCRIPT")], check=True)
		except Exception as err:
			raise InternalError(f"Errore creazione backup: {str(err)}")

	# READ DATABASE
	def get_map_data(self, info_type):
		"""Restituisce un dizionario sui tipi di pagamento nel formato {id_pagamento: nome_pagamento}"""
		_types = {"conti": "MAP_CONTI",
					"spese_varie": "MAP_SPESE_VARIE",
					"entrate": "MAP_ENTRATE"}
		
		if info_type not in _types:
			raise InternalError(f"Tabella di map non trovata con valore: {info_type} - disponibili: {str(_types.keys())}")
		
		sql_string = Tools.format_sql_string_pgsql(operation="S",
											table_name=_types[info_type],
											field_select_list=["ID", "DESCRIZIONE"],
											order_by_dict={"DESCRIZIONE": "ASC"})
		self._exec_sql_string(sql_string, check_return_rows=True)
		info_data = {}
		for row in self.cursor:
			info_data[int(row[0])] = row[1]
		return info_data

	def get_password_from_username(self, username):
		sql_string = Tools.format_sql_string_pgsql(operation="S",
											table_name="WALLET_USERS",
											field_select_list=["PASSWORD"],
											where_dict={"USERNAME": f"'{username}'"})
		self._exec_sql_string(sql_string, check_return_rows=True)
		return self.cursor.fetchval()

	def get_open_deb_creds(self):
		sql_query = Tools.format_sql_string_pgsql(operation='S',
							table_name=f"V_DEBITI_CREDITI_APERTI v",
							field_select_list=["v.*"],
							join_type='I',
							join_table="w_data.MOVIMENTI mv",
							join_dict={"v.ID": "mv.ID"},
							order_by_dict={"mv.DATA_MOV": "DESC", "mv.ID": "DESC"})
		self._exec_sql_string(sql_query=sql_query,check_return_rows=True);

		column_list = []        # lista dei nomi dei campi
		matrix_mov = []         # record di dati
		for column in self.cursor.description:
			if column[0] not in "id":
				column_list.append(column[0])
		for row in self.cursor:
			matrix_mov.append([elem for elem in row])
		return column_list, matrix_mov

	def get_last_n_records(self, id_mov, n_records):
		try:
			sql_query = Tools.format_sql_string_pgsql(operation='S',
							table_name="w_map.MAP_MOVIMENTI",
							field_select_list=["VIEW"],
							where_dict={"ID": id_mov})

			self._exec_sql_string(sql_query=sql_query,check_return_rows=True);
			view_name = self.cursor.fetchone()[0]
			
			sql_query = Tools.format_sql_string_pgsql(operation='S',
							table_name=f"w_data.{view_name} v",
							field_select_list=["v.*"],
							limit=n_records,
							join_type='I',
							join_table="w_data.MOVIMENTI mv",
							join_dict={"v.ID": "mv.ID"},
							order_by_dict={"mv.DATA_MOV": "DESC", "mv.ID": "DESC"})

			self._exec_sql_string(sql_query=sql_query,check_return_rows=True);

			column_list = []        # lista dei nomi dei campi
			matrix_mov = []         # record di dati
			for column in self.cursor.description:
				if column[0] not in "id":
					column_list.append(column[0])
			for row in self.cursor:
				matrix_mov.append([elem for elem in row])
			return column_list, matrix_mov

		except EmptySelectException:
			raise InternalError(f"vista non trovata con id mov: {id_mov}");

	def get_movements(self,):
		sql_string = Tools.format_sql_string_pgsql(operation="S",
											table_name="MAP_MOVIMENTI",
											field_select_list=["ID", "DESCRIZIONE"],
											order_by_dict={"ID": "ASC"})
		self._exec_sql_string(sql_string, check_return_rows=True)
	
		info_data = {}
		for row in self.cursor:
			info_data[int(row[0])] = row[1]
		
		return info_data

	def get_info_mov(self, id_mov):
		result = tuple()
		sql_string = Tools.format_sql_string_pgsql(operation="S",
											table_name="MAP_MOVIMENTI",
											field_select_list=["DESCRIZIONE", "STORED_PROCEDURE"],
											where_dict={"ID": id_mov})
		self._exec_sql_string(sql_string, check_return_rows=True)
		result = self.cursor.fetchone()

		return result[0], result[1]

	# WRITE DATABASE
	def drop_record(self, id_record):
		sql_query = Tools.format_sql_string_pgsql(operation='C',
											 proc_name="REMOVE_MOVEMENT",
											 proc_args=['id_record'])
		self._exec_sql_string(sql_query, {'id_record': id_record}, True)

	def drop_test_mov(self):
		sql_query = Tools.format_sql_string_pgsql(operation='C',
											 proc_name="DROP_TESTS",
											 proc_args=['test_sequence_raw'])
		self._exec_sql_string(sql_query, {'test_sequence_raw': self._seq_test_mov}, True)

	def turn_deb_cred_into_mov(self, id_record):
		sql_query = Tools.format_sql_string_pgsql(operation='C',
											 proc_name="TURN_INTO_MOVEMENT",
											 proc_args=['id_record'])
		self._exec_sql_string(sql_query, {'id_record': id_record}, True)

	def insert_movement(self, id_mov, data_info):
		try:
			type_mov, proc_name = self.get_info_mov(id_mov)
		except EmptySelectException:
			raise InternalError(f"Movimento id: {id_mov} non esistente")

		arg_names_list = []

		if type_mov == "Spesa Varia":
			arg_names_list = ["data_mov", "id_conto", "importo", "test", "id_tipo_s_varia", "descrizione"]
			if "note" in data_info:
				arg_names_list.append("note")

		elif type_mov == "Spesa Fissa":
			arg_names_list = ["data_mov", "id_conto", "importo", "test", "descrizione"]
			if "note" in data_info:
				arg_names_list.append("note")

		elif type_mov == "Stipendio":
			arg_names_list = ["data_mov", "id_conto", "importo", "test", "ddl"]
			if "note" in data_info:
				arg_names_list.append("note")

			if "lordo" in data_info:
				if "note" not in data_info:
					arg_names_list.append("note")
					data_info["note"] = ""
				arg_names_list.append("lordo")

			if "rimborso_spese" in data_info:
				if "note" not in data_info:
					arg_names_list.append("note")
					data_info["note"] = ""
				if "lordo" not in data_info:
					arg_names_list.append("lordo")
					data_info["lordo"] = 0
				arg_names_list.append("rimborso_spese")
			
		elif type_mov == "Entrata":
			arg_names_list = ["data_mov", "id_conto", "importo", "test", "id_tipo_entrata", "descrizione"]
			if "note" in data_info:
				arg_names_list.append("note")

		elif type_mov == "Debito - Credito":
			arg_names_list = ["data_mov", "id_conto", "importo", "test", "deb_cred", "origine", "descrizione"]
			if "note" in data_info:
				arg_names_list.append("note")

		elif type_mov == "Saldo Debito - Credito":
			arg_names_list = ["data_mov", "id_conto", "test", "id_saldo_deb_cred"]
			if "note" in data_info:
				arg_names_list.append("note")
	
			if "importo" in data_info:
				if "note" not in data_info:
					arg_names_list.append("note")
					data_info["note"] = ""
				arg_names_list.append("importo")
 
		elif type_mov == "Spesa di Mantenimento":
			arg_names_list = ["data_mov", "id_conto", "importo", "test", "descrizione"]
			if "note" in data_info:
				arg_names_list.append("note")

		elif type_mov == "Spesa di Viaggio":
			arg_names_list = ["data_mov", "id_conto", "importo", "test", "viaggio", "descrizione"]

			if "note" in data_info:
				arg_names_list.append("note")

		sql_string = Tools.format_sql_string_pgsql(operation="C", proc_name=proc_name, proc_args=arg_names_list)
		self._exec_sql_string(sql_query=sql_string, arguments=data_info, do_commit=True)

	def _exec_sql_string(self, sql_query, arguments={}, do_commit=False, check_return_rows=False):
		try:
			self._logger.debug(f"esecuzione query SQL: '{self.cursor.mogrify(sql_query, arguments).decode('utf-8')}'")
		except KeyError:
			self._logger.error(f"errore logging, argomenti procedura e dati in input non combaciano: '{sql_query}' - args: '{arguments}' inserimento fallito")
			raise AppException('Errore interno, consulta il log per ulteriori dettagli')

		try:
			self.cursor.execute(sql_query, arguments)
		except (psycopg2.Warning, psycopg2.Error) as error:
			self.connection.rollback()
			raise SqlError(f"errore query SQL - trace: {str(error)}")
		else:
			if check_return_rows is True and self.cursor.rowcount == 0:
				raise EmptySelectException("L'istruzione SELECT non ha prodotto risultati")
			if do_commit is True:
				self.connection.commit()


if __name__ == "__main__":
	pass
