from datetime import datetime
from hashlib import sha256              # per creare l'hash di una pwd in input e verificare con quella salvata nel db
import psycopg2                         # info: https://www.psycopg.org/docs/usage.html
import psycopg2.extensions as psycopg2_ext                         # info: https://www.psycopg.org/docs/usage.html
from AppExceptions import *
import Tools                            # funzioni generiche di supporto

class CheckerWallet:
	def check_exist(self, info, exist_field):
		try:
			info[exist_field]
		except KeyError:
			raise WrongInputException(f"Campo {exist_field} mancante")

	def check_text(self, info, text_field):
		try:
			if info[text_field].strip() == "":
				raise WrongInputException(f"Campo {text_field} vuoto")
		except KeyError:
			raise WrongInputException(f"Campo {text_field} mancante")
		else:
			info[text_field] = f"'{info[text_field]}'"

	def check_date(self, info, date_field):
		try:
			datetime.strptime(info[date_field], "%Y-%m-%d")
		except KeyError:
			raise WrongInputException(f"Data mancante")
		except ValueError:
			raise WrongInputException(f"Data non valida: {info[date_field]}")
		else:
			info[date_field] = f"'{info[date_field]}'"

	def check_num(self, info, num_field, check_positivity=False):
		try:
			info[num_field] = Tools.convert_to_float(info[num_field])
		except KeyError:
			raise WrongInputException(f"Importo {num_field} mancante")
		except (TypeError, ValueError):
			raise WrongInputException(f"Importo {num_field} non valido: {info[num_field]}")
		else:
			if check_positivity is True and info[num_field] <= 0:
				raise WrongInputException(f"Importo {num_field} nullo o negativo")
			# info[num_field] = str_number).replace(",", ".")

	def check_id(self, info, id_field):
		try:
			if int(info[id_field]) <= 0:
				raise WrongInputException("ID {id_field} negativo")
		except KeyError:
			raise WrongInputException(f"ID {id_field} mancante")
		except ValueError:
			raise WrongInputException(f"ID {id_field} non valido: {info[id_field]}")
		else:
			info[id_field] = int(info[id_field])


class Wallet:
	def __init__(self, logger=None):
		self.db_name = "wallet"
		self._logger = logger
		self._checker = CheckerWallet()

	def connect(self, host_db, port_db, user, password):
		try:
			self.connection = psycopg2.connect(
				dbname=self.db_name,
				user=user,
				password=password,
				# password=sha256(str(password).encode()).hexdigest(),
				# host=host_db,
				port=port_db
				# require_auth="scram-sha-256"
			)
			# hash_pwd_db = self.get_password_from_username(username)
		except psycopg2.Error as err:
			if "password authentication failed" in str(err):
				raise WrongInputException(f"Wrong password for user {user}")

			tmp = psycopg2.extensions.Diagnostics(err)
			print (tmp, tmp.severity, tmp.sqlstate)
			raise err
			# if wrong_login:
			# else:
			# 	raise SqlError(err.pgerror)
		else:
			self.cursor = self.connection.cursor()
			self.connection.autocommit = False
		# hash_pwd_input = sha256(str(password).encode()).hexdigest()
		# return hash_pwd_input == hash_pwd_db

	def disconnect_database(self):
		self.cursor.close()
		self.connection.close()

	def backup_database(self, backup_path):
		sql_query = Tools.format_sql_string_pgsql(operation='C',
												proc_name="BK_DATABASE",
												proc_args=[f"'{self.db_name}'", f"'{backup_path}'"])
		self._exec_sql_string(sql_query)

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
											order_by_dict={"ID": "DESC"})
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
		sql_string = Tools.format_sql_string_pgsql(operation="S",
											table_name="V_DEBITI_CREDITI_APERTI",
											order_by_dict={"convert(date, DATA, 103)": "DESC"})
		self._exec_sql_string(sql_string, check_return_rows=True)
		column_list = []        # lista dei nomi dei campi
		matrix_mov = []         # record di dati
		for column in self.cursor.description:
			if column[0] != "ID":
				column_list.append(column[0])
		for row in self.cursor:
			matrix_mov.append([elem for elem in row])
		return column_list, matrix_mov

	def get_last_n_records(self, id_mov, n_records):
		pass
		# sql_query = Tools.format_sql_string_pgsql(operation='S',
		# 								   proc_name="READ_MOVEMENTS",
		# 								   proc_args={"id_tipo_mov": id_mov, "n_records": n_records})

		# self._exec_sql_string(sql_query, check_return_rows=True)
		# column_list = []        # lista dei nomi dei campi
		# matrix_mov = []         # record di dati
		# for column in self.cursor.description:
		# 	if column[0] != "ID":
		# 		column_list.append(column[0])
		# for row in self.cursor:
		# 	matrix_mov.append([elem for elem in row])
		# return column_list, matrix_mov

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
										   proc_args=[id_record])
		self._exec_sql_string(sql_query, True)

	def turn_deb_cred_into_mov(self, id_record):
		sql_query = Tools.format_sql_string_pgsql(operation='C',
										   proc_name="TURN_INTO_MOVEMENT",
										   proc_args=[id_record])
		self._exec_sql_string(sql_query, True)

	def insert_movement(self, id_mov, data_info):
		try:
			type_mov, proc_name = self.get_info_mov(id_mov)
		except EmptySelectException:
			raise InternalError(f"Movimento id: {id_mov} non esistente")

		proc_args = []
		if type_mov == "Spesa Varia":
			proc_args = self._format_args_spesa_varia(data_info)
		elif type_mov == "Spesa Fissa":
			proc_args = self._format_args_spesa_fissa(data_info)
		elif type_mov == "Stipendio":
			proc_args = self._format_args_stipendio(data_info)
		elif type_mov == "Entrata":
			proc_args = self._format_args_entrata(data_info)
		elif type_mov == "Debito - Credito":
			proc_args = self._format_args_debito_credito(data_info)
		elif type_mov == "Saldo Debito - Credito":
			proc_args = self._format_args_saldo_debito_credito(data_info)
		elif type_mov == "Spesa di Mantenimento":
			proc_args = self._format_args_spesa_mantenimento(data_info)
		elif type_mov == "Spesa di Viaggio":
			proc_args = self._format_args_spesa_viaggio(data_info)
		print(proc_args)
		sql_string = Tools.format_sql_string_pgsql(operation="C", proc_name=proc_name, proc_args=proc_args)
		self._exec_sql_string(sql_string, True)

	def _format_args_spesa_varia(self, data):
		self._checker.check_date(data, "data_mov")
		self._checker.check_id(data, "id_conto")
		self._checker.check_num(data, "importo", True)
		self._checker.check_text(data, "descrizione")
		self._checker.check_id(data, "id_tipo_s_varia")
		
		proc_args = [data["data_mov"], data["id_conto"], data["importo"], data["id_tipo_s_varia"], data["descrizione"]]
		
		if "note" in data:
			self._checker.check_text(data, "note")
			proc_args.append(data["note"])

		return proc_args

	def _format_args_spesa_fissa(self, data):
		self._checker.check_date(data, "data_mov")
		self._checker.check_id(data, "id_conto")
		self._checker.check_num(data, "importo", True)
		self._checker.check_text(data, "descrizione")
		
		proc_args = [data["data_mov"], data["id_conto"], data["importo"], data["descrizione"]]
		
		if "note" in data:
			self._checker.check_text(data, "note")
			proc_args.append(data["note"])

		return proc_args
	
	def _format_args_stipendio(self, data):
		self._checker.check_date(data, "data_mov")
		self._checker.check_id(data, "id_conto")
		self._checker.check_num(data, "importo", True)
		self._checker.check_text(data, "ddl")
		
		proc_args = [data["data_mov"], data["id_conto"], data["importo"], data["ddl"]]

		if "note" in data:
			self._checker.check_text(data, "note")
			proc_args.append(data["note"])

		if "netto" in data:
			self._checker.check_num(data, "netto", True)
			proc_args.append(data["netto"])
		
		if "rimborso_spese" in data:
			self._checker.check_num(data, "rimborso_spese", True)
			proc_args.append(data["rimborso_spese"])

		return proc_args
	
	def _format_args_entrata(self, data):
		self._checker.check_date(data, "data_mov")
		self._checker.check_id(data, "id_conto")
		self._checker.check_num(data, "importo", True)
		self._checker.check_id(data, "id_tipo_entrata")
		self._checker.check_text(data, "descrizione")

		proc_args = [data["data_mov"], data["id_conto"], data["importo"], data["id_tipo_entrata"], data["descrizione"]]
		
		if "note" in data:
			self._checker.check_text(data, "note")
			proc_args.append(data["note"])

		return proc_args

	def _format_args_debito_credito(self, data):
		self._checker.check_date(data, "data_mov")
		self._checker.check_id(data, "id_conto")
		self._checker.check_num(data, "importo", True)
		self._checker.check_exist(data, "deb_cred")
		self._checker.check_text(data, "origine")
		self._checker.check_text(data, "descrizione")
		
		proc_args = [data["data_mov"], data["id_conto"], data["importo"], data["deb_cred"], data["origine"], data["descrizione"]]
		
		if "note" in data:
			self._checker.check_text(data, "note")
			proc_args.append(data["note"])

		return proc_args

	def _format_args_saldo_debito_credito(self, data):
		self._checker.check_date(data, "data_mov")
		self._checker.check_id(data, "id_conto")
		self._checker.check_text(data, "id_saldo_deb_cred")

		proc_args = [data["data_mov"], data["id_conto"], data["id_saldo_deb_cred"]]
		
		if "importo" in data:
			self._checker.check_num(data, "importo", True)
			proc_args.append(data["importo"])

		if "note" in data:
			self._checker.check_text(data, "note")
			proc_args.append(data["note"])

		return proc_args

	def _format_args_spesa_mantenimento(self, data):
		self._checker.check_date(data, "data_mov")
		self._checker.check_id(data, "id_conto")
		self._checker.check_num(data, "importo", True)
		self._checker.check_text(data, "descrizione")

		proc_args = [data["data_mov"], data["id_conto"], data["importo"], data["descrizione"]]
		
		if "note" in data:
			self._checker.check_text(data, "note")
			proc_args.append(data["note"])

		return proc_args

	def _format_args_spesa_viaggio(self, data):
		self._checker.check_date(data, "data_mov")
		self._checker.check_id(data, "id_conto")
		self._checker.check_num(data, "importo", True)
		self._checker.check_text(data, "viaggio")
		self._checker.check_text(data, "descrizione")

		proc_args = [data["data_mov"], data["id_conto"], data["importo"], data["viaggio"], data["descrizione"]]
		
		if "note" in data:
			self._checker.check_text(data, "note")
			proc_args.append(data["note"])

		return proc_args

	def _exec_sql_string(self, sql_query, do_commit=False, check_return_rows=False):
		self._logger.debug("esecuzione query SQL: '%s'", sql_query)
		try:
			self.cursor.execute(sql_query)
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



