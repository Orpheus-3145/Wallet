from datetime import datetime
# import pyodbc                           # per la connessione al db SQL Server
from hashlib import sha256              # per creare l'hash di una pwd in input e verificare con quella salvata nel db

from AppExceptions import *
import Tools                            # funzioni generiche di supporto


class Wallet:
    def __init__(self, dsn, logger=None):
        self.logger = logger
        # try:
        #     self.connection = pyodbc.connect(dsn)       # autocommit = False default
        #     self.cursor = self.connection.cursor()
        # except pyodbc.Error as error:
        #     raise SqlError(error.args[1])
        # else:
        #     self.db_name = "Wallet"
        #     self.movements = self.get_info_db("movimenti")

    def login_wallet(self, username, password):
        hash_pwd_db = self.get_password_from_username(username)
        hash_pwd_input = sha256(str(password).encode()).hexdigest()
        return hash_pwd_input == hash_pwd_db

    def insert_movement(self, id_mov, data_info):
        if id_mov not in self.movements:
            raise InternalError("ID {} movimento sconosciuto".format(id_mov))
        sp_name = ""
        keys_to_check = ["importo", "id_conto"]
        keys_date_to_check = ["data_mov"]
        keys_float_to_check = ["importo"]
        keys_id_to_check = ["id_conto"]
        keys_varchar = ["data_mov", "note"]
        if self.movements[id_mov] == "Spesa Varia":
            keys_to_check.extend(["id_tipo_s_varia", "descrizione"])
            keys_id_to_check.append("id_tipo_s_varia")
            keys_varchar.append("descrizione")
            sp_name = "INSERISCI_S_VARIA"
        elif self.movements[id_mov] == "Spesa Fissa":
            keys_to_check.append("descrizione")
            keys_varchar.append("descrizione")
            sp_name = "INSERISCI_S_FISSA"
        elif self.movements[id_mov] == "Stipendio":
            keys_to_check.append("ddl")
            keys_varchar.append("ddl")
            keys_float_to_check.extend(["netto", "rimborso_spese"])
            sp_name = "INSERISCI_STIPENDIO"
        elif self.movements[id_mov] == "Entrata":
            keys_to_check.extend(["id_tipo_entrata", "descrizione"])
            keys_id_to_check.append("id_tipo_entrata")
            keys_varchar.append("descrizione")
            sp_name = "INSERISCI_ENTRATA"
        elif self.movements[id_mov] == "Debito - Credito":
            keys_to_check.extend(["deb_cred", "origine", "descrizione"])
            keys_id_to_check.append("deb_cred")
            keys_varchar.extend(["origine", "descrizione"])
            sp_name = "INSERISCI_DEB_CRED"
        elif self.movements[id_mov] == "Saldo Debito - Credito":
            keys_to_check.append("id_saldo_deb_cred")
            keys_to_check.remove("importo")
            keys_varchar.append("id_saldo_deb_cred")
            sp_name = "SALDA_DEB_CRED"
        elif self.movements[id_mov] == "Spesa di Mantenimento":
            keys_to_check.append("descrizione"),
            keys_varchar.append("descrizione")
            sp_name = "INSERISCI_S_MANTENIMENTO"
        elif self.movements[id_mov] == "Spesa di Viaggio":
            keys_to_check.extend(["viaggio", "descrizione"]),
            keys_varchar.extend(["viaggio", "descrizione"])
            sp_name = "INSERISCI_S_VIAGGIO"
        self.check_movement(data_info, keys_to_check, keys_date_to_check, keys_float_to_check, keys_id_to_check)
        self.run_sp(sp_name, data_info, keys_varchar)

    def check_movement(self, movement, keys_to_check, keys_date_to_check, keys_float_to_check, keys_id_to_check):
        for key_to_check in keys_to_check:
            if key_to_check not in movement or movement[key_to_check].strip() == "":
                raise WrongValueInsert("Informazioni mancanti")
        for date_key in keys_date_to_check:
            if date_key in movement:
                try:
                    datetime.strptime(movement[date_key], "%Y-%m-%d")
                except (KeyError, ValueError):
                    raise WrongValueInsert(f"Data non valida: {movement[date_key]}")
        for numeric_key in keys_float_to_check:
            if numeric_key in movement:
                try:
                    movement[numeric_key] = Tools.convert_to_float(movement[numeric_key])
                    if movement[numeric_key] <= 0:
                        raise WrongValueInsert("Importo nullo o negativo")
                except (TypeError, ValueError):
                    raise WrongValueInsert(f"Importo non valido: {movement[numeric_key]}")
        for id_key in keys_id_to_check:
            if id_key in movement:
                try:
                    int(movement[id_key])
                except ValueError:
                    raise WrongValueInsert(f"ID non valido: {movement[id_key]}")

    def run_sp(self, sp_name, sp_args=None, keys_varchar=None, do_commit=True):
        sql_query = self.format_sql_string(suide='E',
                                           sp_name=sp_name,
                                           sp_args=sp_args,
                                           keys_varchar=keys_varchar)
        self.exec_query_sql(sql_query, do_commit)

    def exec_query_sql(self, sql_query, do_commit=False):
        if self.logger:
            self.logger.debug("esecuzione query SQL: '%s'", sql_query)
        try:
            self.cursor.execute(sql_query)
        except pyodbc.Error as err:
            self.cursor.rollback()
            raise SqlError(err.args[1])
        else:
            if do_commit is True:
                self.cursor.commit()

    def close_wallet(self):
        """concludo il log"""
        self.cursor.close()
        self.connection.close()

    def backup_database(self, backup_path):
        sp_args = {"bk_path": backup_path, "db_to_backup": self.db_name}
        keys_varchar = sp_args.keys()
        try:        # running a sp that creates the backup always fails the first time even though is outside a transaction and autocommit is False
            self.run_sp(sp_name="BK_DATABASE", sp_args=sp_args, keys_varchar=keys_varchar, do_commit=False)
        except SqlError:    # the second time the backup is created (?)
            self.run_sp(sp_name="BK_DATABASE", sp_args=sp_args, keys_varchar=keys_varchar, do_commit=False)

    # READ DATABASE
    def get_info_db(self, info_type):
        """Restituisce un dizionario sui tipi di pagamento nel formato {id_pagamento: nome_pagamento}"""
        _types = {"movimenti": "MAP_MOVIMENTI",
                  "conti": "MAP_CONTI",
                  "spese_varie": "MAP_SPESE_VARIE",
                  "entrate": "MAP_ENTRATE"}
        if info_type not in _types:
            raise InternalError("Tabella di map non trovata con valore: {}".format(info_type))
        sql_string = self.format_sql_string(suide="S",
                                            table_name=_types[info_type],
                                            field_select_list=["ID", "DESCRIZIONE"],
                                            order_by_dict={"ID": "DESC"})
        self.exec_query_sql(sql_string)
        info_data = {}
        for row in self.cursor:
            info_data[int(row.ID)] = row.DESCRIZIONE
        return info_data

    def get_password_from_username(self, username):
        sql_string = self.format_sql_string(suide="S",
                                            table_name="WALLET_USERS",
                                            field_select_list=["PASSWORD"],
                                            where_dict={"USERNAME": username},
                                            keys_varchar=[username])
        self.exec_query_sql(sql_string)
        return self.cursor.fetchval()

    def get_bi_credentials(self, role="ADMIN"):
        sql_string = self.format_sql_string(suide="S",
                                            table_name="QLIK_USERS",
                                            field_select_list=["username", "password"],
                                            where_dict={"RUOLO": role},
                                            keys_varchar=[role])
        self.exec_query_sql(sql_string)
        row = self.cursor.fetchone()
        return row.username, row.password

    def get_open_deb_creds(self):
        sql_string = self.format_sql_string(suide="S",
                                            table_name="V_DEBITI_CREDITI_APERTI",
                                            order_by_dict={"convert(date, DATA, 103)": "DESC"})
        self.exec_query_sql(sql_string)
        column_list = []        # lista dei nomi dei campi
        matrix_mov = []         # record di dati
        for column in self.cursor.description:
            if column[0] != "ID":
                column_list.append(column[0])
        for row in self.cursor:
            matrix_mov.append([elem for elem in row])
        return column_list, matrix_mov

    def get_last_n_records(self, id_mov, n_records):
        self.run_sp(sp_name="READ_MOVEMENTS",
                    sp_args={"id_tipo_mov": id_mov, "n_records": n_records},
                    do_commit=False)
        column_list = []        # lista dei nomi dei campi
        matrix_mov = []         # record di dati
        for column in self.cursor.description:
            if column[0] != "ID":
                column_list.append(column[0])
        for row in self.cursor:
            matrix_mov.append([elem for elem in row])
        return column_list, matrix_mov

    # WRITE DATABASE
    def drop_record(self, id_record):
        self.run_sp(sp_name="REMOVE_MOVEMENT", sp_args={"id_mov_to_drop": id_record})

    def turn_deb_cred_into_mov(self, id_record):
        self.run_sp(sp_name="TURN_INTO_MOVEMENT", sp_args={"id_record": id_record})

    def format_sql_string(self, suide, table_name=None, field_select_list=None, where_dict=None, update_dict=None,
                          insert_dict=None, join_type=None, join_table=None, join_dict=None, keys_varchar=None,
                          order_by_dict=None, top=None, sp_name=None, sp_args=None):
        """Crea e formatta un'instruzione SQL di tipo suid (SELECT, UPDATE, INSERT, DELETE)
            - suide -> ha come valore 'S' SELECT, 'U' UPDATE, 'I' INSERT, 'D' DELETE, 'E' EXEC
            - table_name -> nome tabella,
            - field_select_list -> lista di campi da selezionare/modificare/inserire/cancellare
            - where_dict -> dizionario che contiene n condizioni che devono essere interamente soddisfatte (AND ... AND ... ) nella forma chiave = valore inseriti nel costrutto WHERE
            - update_dict -> dizionario in cui chaive (<-campo) = valore nel costrutto SET di UPDATE
            - insert_dict -> dizionario contenete il campo (chiave) e il valore da inserire in esso nel costrutto INSERT INTO
            - join -> tipo di join da eseguire -> 'I' inner, 'L' left, 'R' right, 'C' cross
            - join_table -> tabella da joinare
            - join_fields -> dizionario di campi da uguagliare per il join
            - keys_varchar -> lista di valori varchar da inserire in select, where, insert o update, restituisce il valore nello statement SQL racchiuso da singoli apici
            - order_by_dict -> coppie CAMPO: DESC/ASC
            - top -> se diverso da None mostra le prime top (int) righe
            - sp_name -> nome procedura da eseguire
            - sp_args -> dizionario nella forma {nome_argomento: valore_argomento}"""
        sql_string = ""

        if suide == 'S':
            sql_string = "SELECT * FROM {}".format(table_name)
            if top is not None:  # inserisco top x nella select
                if str(top).isdigit():
                    top_n_values = "top {}".format(int(top))
                    sql_string = sql_string.replace("SELECT", "SELECT {}".format(top_n_values))
                else:
                    raise WrongValueInsert("Non è stato passato un valore numerico per il numero di record da selezionare")
            if isinstance(field_select_list, list):  # field_select_list <> None rimuovo '*' e creo l'elenco dei campi
                fields_to_select = ", ".join(field_select_list)
                sql_string = sql_string.replace("*", fields_to_select)
            # elif field_select_list:
            #     raise WrongValueInsert("è stato passato un parametro non valido per la condizione SELECT, deve essere list")
            if join_dict and join_table and join_type:
                join_types_dict = {"I": "INNER JOIN", "L": "LEFT JOIN", "R": "RIGHT JOIN", "C": "CROSS JOIN"}
                if join_type in join_types_dict and isinstance(join_dict, dict):  # in questo caso devo inserire anche un join
                    fields_to_join = " AND ".join("{} = {}".format(key, value) for key, value in join_dict.items())
                    sql_string = " ".join(
                        [sql_string, join_types_dict.get(join_type), join_table, "ON", fields_to_join])
                # else:
                #     raise WrongValueInsert("per join richiesti parametri validi join_type e join_table")
            if isinstance(where_dict, dict):  # se where_dict <> da None aggiungo anche le restrizioni tramite WHERE statement
                fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else value) for key, value in where_dict.items())
                sql_string = " ".join([sql_string, "WHERE", fields_to_filter])
            # elif where_dict:
            #     raise WrongValueInsert("è stato passato un parametro non valido per la condizione WHERE, deve essere dict")
            if isinstance(order_by_dict, dict):  # se order_by_dict <> da None inserisco l'ordinamento
                fields_to_order_by = ", ".join("{} {}".format(key, value) for key, value in order_by_dict.items())
                sql_string = " ".join([sql_string, "ORDER BY", fields_to_order_by])
            # elif order_by_dict:
            #     raise WrongValueInsert("è stato passato un parametro non valido per la condizione ORDER BY, deve essere dict")
        elif suide == 'U':
            sql_string = "UPDATE {} SET".format(table_name)
            if not isinstance(update_dict, dict):
                raise WrongValueInsert("Non è stata fornita la lista dei campi da modificare oppure il tipo non è corretto, deve essere dict")
            fields_to_update = ", ".join("{} = {}".format(key, "'{}'".format(
                Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else value) for
                                         key, value in
                                         update_dict.items())
            sql_string = " ".join([sql_string, fields_to_update])
            if isinstance(where_dict, dict):  # se where_dict è tipo dict aggiungo anche le restrizioni tramite WHERE statement
                fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else value) for
                                                key, value in
                                                where_dict.items())
                sql_string = " ".join([sql_string, "WHERE", fields_to_filter])
            # elif where_dict is not None:
            #     raise WrongValueInsert("è stato passato un parametro non valido per la condizione WHERE, deve essere dict")
            else:  # cautela personale per non modificare una tabella per intero
                raise WrongValueInsert("Non si può modificare interamente una tabella")
        elif suide == 'I':
            if isinstance(insert_dict, dict):  # mi accerto che venga fornita la lista dei campi e il loro relativo valore da aggiungere
                sql_string = "INSERT INTO {}".format(table_name)
                fields_to_insert = "({})".format(", ".join(insert_dict.keys()))  # elenco campi da inserire
                values_to_insert = "({})".format(", ".join(["'{}'".format(
                    Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else str(value) for value in insert_dict.values()]))
                sql_string = " ".join([sql_string, fields_to_insert, "VALUES", values_to_insert])
            elif insert_dict is not None:
                raise WrongValueInsert("è stato passato un parametro non valido per la condizione INSERT, deve essere dict")
            else:
                raise WrongValueInsert("Non è stata fornita la lista dei campi da inserire!")
        elif suide == 'D':
            sql_string = "DELETE {}".format(table_name)
            if isinstance(where_dict, dict):  # non voglio mai cancellare per intero la tabella, faccio sì che debbano esserci sempre clausole WHERE
                fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else value) for key, value in where_dict.items())
                sql_string = " ".join([sql_string, "WHERE", fields_to_filter])
            elif where_dict is not None:
                raise WrongValueInsert("è stato passato un parametro non valido per la condizione WHERE, deve essere dict")
            else:
                raise WrongValueInsert("Non è possibile eliminare per intero una tabella!")
        elif suide == "E":
            sql_string = "exec {} ".format(sp_name)
            if sp_args is not None:
                str_args = []
                for arg_name, arg_value in sp_args.items():
                    if keys_varchar and arg_name in keys_varchar:
                        str_args.append("@{}='{}'".format(arg_name, Tools.escape_sql_chars(arg_value)))
                    else:
                        str_args.append("@{}={}".format(arg_name, arg_value))
                sql_string = sql_string + ", ".join(str_args)
        return sql_string


if __name__ == "__main__":
    pass



