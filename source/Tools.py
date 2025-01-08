import os.path


class WrongInputSqlFormat(Exception):
	"""Quando i parametri di format_sql_string() non sono corretti"""
	def __init__(self, error_text):
		super().__init__()
		self.error_text = error_text  # creo la proprietà di classe per avere maggiori informazioni sull'errore verificatosi

	def __str__(self):
		return self.error_text
	

def convert_to_float(str_number):
	"""Questa funzione riceve una stringa che rappresenta un float e, se presenti virgole, le sostituisce con i punti;
	eventualmente restituisce la stringa convertita in int o float"""
	return float(str(str_number).replace(",", "."))


def get_abs_path(relative_path):
	abs_path = os.path.normpath(os.path.join(os.getcwd(), relative_path))
	if os.path.exists(abs_path) is False:
		raise ValueError("non-existing path: {}".format(abs_path))
	return abs_path

def format_sql_string_pgsql(operation, table_name="", field_select_list=[], where_dict={}, update_dict={},
						  insert_dict={}, join_type={}, join_table="", join_dict={},
						  order_by_dict={}, limit=-1, proc_name="", proc_args=[], safe_mode=True):
	"""Crea e formatta un'instruzione SQL di tipo suid (SELECT, UPDATE, INSERT, DELETE)
		- operation -> ha come valore 'S' SELECT, 'U' UPDATE, 'I' INSERT, 'D' DELETE, 'E' EXEC
		- table_name -> nome tabella,
		- field_select_list -> lista di campi da selezionare/modificare/inserire/cancellare
		- where_dict -> dizionario che contiene n condizioni che devono essere interamente soddisfatte (AND ... AND ... ) nella forma chiave = valore inseriti nel costrutto WHERE
		- update_dict -> dizionario in cui chaive (<-campo) = valore nel costrutto SET di UPDATE
		- insert_dict -> dizionario contenete il campo (chiave) e il valore da inserire in esso nel costrutto INSERT INTO
		- join_type -> tipo di join da eseguire -> 'I' inner, 'L' left, 'R' right, 'C' cross
		- join_table -> tabella da joinare
		- join_fields -> dizionario di campi da uguagliare per il join
		- keys_varchar -> lista di valori varchar da inserire in select, where, insert o update, restituisce il valore nello statement SQL racchiuso da singoli apici
		- order_by_dict -> coppie CAMPO: DESC/ASC
		- limit -> se diverso da None mostra le prime limit (int) righe
		- proc_name -> nome procedura da eseguire
		- proc_args -> lista degli argomenti della procedura"""
	sql_string = ""

	if operation == 'S':
		field_list = "*"
		fields_to_join = ""
		fields_to_filter = ""
		fields_to_order = ""
		_join_types_dict = {"I": "INNER", "L": "LEFT", "R": "RIGHT", "C": "CROSS"}
		
		if field_select_list:
			field_list = ", ".join(field_select_list)
		
		sql_string = f"SELECT {field_list} FROM {table_name}"

		if join_dict and join_table and join_type in _join_types_dict:
			fields_to_join = " AND ".join("{} = {}".format(key, value) for key, value in join_dict.items())
			sql_string = f"{sql_string} {_join_types_dict.get(join_type)} JOIN {join_table} ON {fields_to_join}"
		
		if where_dict:
			fields_to_filter = " AND ".join("{} = {}".format(key, value) for key, value in where_dict.items())
			sql_string = f"{sql_string} WHERE {fields_to_filter}"

		if order_by_dict:
			fields_to_order = ", ".join("{} {}".format(key, value) for key, value in order_by_dict.items())
			sql_string = f"{sql_string} ORDER BY {fields_to_order}"

		if limit != -1:
			sql_string = f"{sql_string} LIMIT {limit}"

	elif operation == 'U':
		fields_to_update = ""
		fields_to_filter = ""
		
		if not update_dict:
			raise WrongInputSqlFormat("Non è stata fornita la lista dei campi da modificare")
		
		fields_to_update = ", ".join("{} = {}".format(key, value) for key, value in update_dict.items())
		sql_string = f"UPDATE {table_name} SET {fields_to_update}"

		if where_dict:
			fields_to_filter = " AND ".join("{} = {}".format(key, value) for key, value in where_dict.items())
			sql_string = f"{sql_string} WHERE {fields_to_filter}"
		elif safe_mode is True:  # cautela personale per non modificare una tabella per intero
			raise WrongInputSqlFormat("Non si può modificare interamente una tabella")

	elif operation == 'I':
		fields_to_insert = ""
		values_to_insert = ""

		if not insert_dict:
			raise WrongInputSqlFormat("Non è stata fornita la lista dei campi da modificare oppure il tipo non è corretto, deve essere dict")
	   
		fields_to_insert = ", ".join(insert_dict.keys())  # elenco campi da inserire
		values_to_insert = ", ".join(insert_dict.values())  # elenco campi da inserire
		
		sql_string = f"INSERT INTO {table_name} ({fields_to_insert} VALUES ({values_to_insert}))"

	elif operation == 'D':
		sql_string = f"DELETE {table_name}"
		
		if where_dict:
			fields_to_filter = " AND ".join("{} = {}".format(key, value) for key, value in where_dict.items())
			sql_string = f"{sql_string} WHERE {fields_to_filter}"
		elif safe_mode is True:  # cautela personale per non modificare una tabella per intero
			raise WrongInputSqlFormat("Non si può cancellare interamente una tabella")

	elif operation == "C":
		arguments = ""
		if proc_args:
			arguments = ", ".join([f"%({arg_name})s" for arg_name in proc_args])
		sql_string = f"CALL {proc_name} ({arguments})"

	return sql_string + ';'

# NB fix con $$
def escape_sql_chars(str_input):
	"""Esegue l'escaping dei caratteri problematici per le stringe SQL , per esempio il carattere ' """
	return str(str_input).replace("'", "''")


def list_to_str(container):
	"""Converte in stringa un contenitore passato (list, dict, ...)"""
	str_elements = ""
	if isinstance(container, list) or isinstance(container, set):
		str_elements += ", ".join([str(element) for element in container])
	elif isinstance(container, dict):
		str_elements += ", ".join("{}: {}".format(key, value) for key, value in container.items())

	return str_elements


def str_to_list_float(string_list):
	try:
		return [float(value) for value in string_list[1:-1].split(",")]
	except (TypeError, ValueError, IndexError):
		raise ValueError("invalid format [usage: '[a, b, c, ..., k]']")


if __name__ == "__main__":
	pass
