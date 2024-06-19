import win32com.client as win32         # per aprire applicazioni win
import pywintypes                       # per gestire alcune eccezioni legate al modulo di cui sopra
import time
from datetime import datetime, date
import pyodbc                           # per la connessione al db SQL Server
import os.path                          # per gestire i path
import logging                          # per gestire il log
import Tools                            # funzioni generiche di supporto
from hashlib import sha256              # per creare l'hash di una pwd in input e verificare con quella salvata nel db
from functools import partial


class WrongValueInsert(Exception):
    """Eccezione che viene sollevata in caso in cui uno dei dati passati, da inserire in un movimento, non sia corretto"""

    def __init__(self, error_text):
        super().__init__()
        self.error_text = error_text  # creo la proprietà di classe per avere maggiori informazioni sull'errore verificatosi

    def __str__(self):
        return self.error_text


class FatalError(Exception):
    """Errore generico di natura fatale, non riconducibile all'errore di un utente ma ad un errore del programma
    (esclusi quelli relativi al database e SQL)."""

    def __init__(self, error_text):
        super().__init__()
        self.error_text = error_text  # creo la proprietà di classe per avere maggiori informazioni sull'errore verificatosi

    def __str__(self):
        return self.error_text


class QlikViewApp:
    """App che permette di aprire un file di QlikView"""

    def __init__(self, bi_path):
        """bi_path è il percorso del file qlik, le altre due proprietà verranno inizializzate nel metodo open()"""

        self.app = None             # applicazione di QlikView
        self.current_file = None    # istanza del file qlik

        if os.path.exists(bi_path):
            if os.path.splitext(bi_path)[1] != ".qvw":
                logging.error("[%-10s]: Creazione app pywin32 - errore - il file passato non ha estensione .qvw" % "BI")
                raise FatalError("Il file di BI non ha estensione .qvw")
            else:
                self.bi_path = os.path.dirname(bi_path)    # percorso del file qlik
                self.bi_name = os.path.basename(bi_path)   # nome del file qlik
        else:
            logging.error("[%-10s]: Creazione app pywin32 - errore - il percorso %s non esiste", "BI", bi_path)
            raise FatalError("Il percorso passato non esiste")

    def open(self, user=None, pwd=None):
        """Apertura del file qlik"""
        try:
            self.app = win32.Dispatch('QlikTech.QlikView')

        except pywintypes.com_error as error:
            logging.error("[%-10s]: Apertura file di BI - errore - trace: %s", "BI", str(error))
            raise FatalError("Errore di QlikView, consulta il log per maggiori dettagli")

        else:
            self.current_file = self.app.OpenDoc(os.path.join(os.getcwd(), self.bi_path, self.bi_name), user, pwd)
            logging.info("[%-10s]: Apertura file di BI - aperto file di BI in %s", "BI", os.path.join(self.bi_path, self.bi_name))

        return self.current_file

    def close(self):
        """Attualmente questo metodo non viene mai chiamato"""
        try:
            if self.current_file:
                self.current_file.CloseDoc()

            self.app.Quit()

        except AttributeError:      # se chiudo il file qlik prima dell'app ho queso errore 'strano', lo ignoro
            pass


class Wallet:
    """Gestisce le comunicazioni tra dati in input e il loro inserimento nel database, oltre ad azioni secondarie
    quali recuperare le credenziali dell'app, della BI, oppure di aggiornare un log su tutte le operazioni fatte sul
    db"""

    def __init__(self, dsn):
        """Creo la connessione al database tramite il dsn"""
        self.name = "Wallet"
        self._dsn = dsn
        try:
            self.connection = pyodbc.connect(self._dsn)
            self.cursor = self.connection.cursor()
        except pyodbc.Error as error:
            logging.error("[%-10s]: avvio istanza - errore - trace: %s", self.name, str(error))
            raise FatalError("Errore nella connessione al database, consulta il log per maggiori dettagli")
        else:
            logging.info("[%-10s]: %s", self.name, "*" * 80)
            logging.info("[%-10s]: avvio istanza - creazione di un'istanza di Wallet e connessione al database riuscita" % self.name)
            self.mov_info = {}
            self.fill_movements()

    def fill_movements(self):
        sql_string = self.format_sql_string(suide="S",
                                            table_name="MAP_MOVIMENTI",
                                            field_select_list=["ID", "DESCRIZIONE", "STORED_PROCEDURE"],
                                            order_by_dict={"ID": "DESC"})
        self.exec_query_sql(sql_string)
        for row in self.cursor:
            self.mov_info[int(row.ID)] = (row.DESCRIZIONE, row.STORED_PROCEDURE)

    def login_wallet(self, username, password):
        """Tenta il login con user e pwd"""
        hash_pwd_db = self.get_password_from_username(username)
        hash_pwd_input = sha256(str(password).encode()).hexdigest()
        return hash_pwd_input == hash_pwd_db

    def insert_movement(self, id_mov, data_info):
        if self.mov_info == {}:
            logging.error("[%-10s]: movimenti mancanti, chiamare fill_movements()", self.name)
            raise FatalError("Errore interno, consulta il log per maggiori dettagli")
        elif id_mov not in self.mov_info:
            raise WrongValueInsert("Unknown movement ID: {}".format(id_mov))
        type_mov = self.mov_info[id_mov][0]
        sp_name = self.mov_info[id_mov][1]
        keys_to_check = ["importo", "id_tipo_pag"]
        keys_date_to_check = ["str_data_mov"]
        keys_float_to_check = ["importo"]
        keys_id_to_check = ["id_tipo_pag"]
        keys_varchar = ["str_data_mov", "note"]
        if type_mov == "Spesa Generica":
            keys_to_check.extend(["id_tipo_s_varia", "descrizione"])
            keys_id_to_check.append("id_tipo_s_varia")
            keys_varchar.append("descrizione")
        elif type_mov == "Spesa Fissa":
            keys_to_check.append("descrizione")
            keys_varchar.append("descrizione")
        elif type_mov == "Stipendio":
            keys_to_check.append("ddl")
            keys_varchar.append("ddl")
            keys_float_to_check.extend(["netto", "rimborso_spese"])
        elif type_mov == "Entrata":
            keys_to_check.extend(["id_tipo_entrata", "descrizione"])
            keys_id_to_check.append("id_tipo_entrata")
            keys_varchar.append("descrizione")
        elif type_mov == "Debito - Credito":
            keys_to_check.extend(["deb_cred", "origine", "descrizione"])
            keys_id_to_check.append("deb_cred")
            keys_varchar.extend(["origine", "descrizione"])
        elif type_mov == "Saldo Debito - Credito":
            keys_to_check.append("id_saldo_deb_cred")
            keys_to_check.remove("importo")
            keys_varchar.append("id_saldo_deb_cred")
        elif type_mov == "Spesa di Mantenimento":
            keys_to_check.append("descrizione"),
            keys_varchar.append("descrizione")
        elif type_mov == "Spesa di Viaggio":
            keys_to_check.extend(["viaggio", "descrizione"]),
            keys_varchar.extend(["viaggio", "descrizione"])

        self.check_movement(type_mov, data_info, keys_to_check, keys_date_to_check, keys_float_to_check, keys_id_to_check)
        self.run_sp(sp_name, data_info, keys_varchar)
        time.sleep(0.1)  # metto in pausa per 0.1 secondi per evitare che la (bassa) precisione di DATETIME di SQL scriva valori uguali
        logging.info("[%-10s]: inserito nuovo movimento", self.name)

    def check_movement(self, type_mov, movement, keys_to_check, keys_date_to_check, keys_float_to_check, keys_id_to_check):
        for key_to_check in keys_to_check:
            if key_to_check not in movement or movement[key_to_check].strip() == "":
                raise WrongValueInsert("Informazioni mancanti")
        for date_key in keys_date_to_check:
            if date_key in movement:
                try:
                    datetime.strptime(movement[date_key], "%d/%m/%Y")
                except (KeyError, ValueError):
                    raise WrongValueInsert("Data non valida")
        for numeric_key in keys_float_to_check:
            if numeric_key in movement:
                try:
                    if Tools.convert_to_float(movement[numeric_key]) <= 0:
                        raise WrongValueInsert("Importo nullo o negativo")
                except (TypeError, ValueError):
                    raise WrongValueInsert("Importo non valido")
        for id_key in keys_id_to_check:
            if id_key in movement:
                try:
                    int(movement[id_key])
                except ValueError:
                    raise WrongValueInsert("ID non valido" + movement[id_key])

    def run_sp(self, sp_name, sp_args=None, keys_varchar=None):
        sql_query = self.format_sql_string(suide='E',
                                           sp_name=sp_name,
                                           sp_args=sp_args,
                                           keys_varchar=keys_varchar)
        self.exec_query_sql(sql_query)
        self.cursor.commit()

    def exec_query_sql(self, sql_query):
        try:
            print(sql_query)
            logging.debug("[%-10s]: esecuzione della query: %s", self.name, sql_query)
            self.cursor.execute(sql_query)
        except pyodbc.Error as err:
            logging.error("[%-10s]: errore - trace: %s", self.name, str(err))
            self.cursor.rollback()
            raise FatalError("Errore nel database, consulta il log per maggiori dettagli")

    def close_wallet(self):
        """concludo il log"""
        self.cursor.close()
        self.connection.close()
        logging.info("[%-10s]: chiusura di wallet" % self.name)
        logging.info("[%-10s]: %s", self.name, "*" * 80)

    def backup_database(self, backup_path):
        backup_name = "{}_{}.bak".format(self.name, datetime.now().strftime("%d-%m-%Y"))
        if not os.path.isabs(backup_path):
            backup_path = os.path.normpath(os.path.join(os.getcwd(), backup_path))
        count = 1
        while os.path.exists(os.path.join(backup_path, backup_name)):
            backup_name = "{}_{}_{}.bak".format(self.name, datetime.now().strftime("%d-%m-%Y"), count)
            count += 1
        backup_path = os.path.join(backup_path, backup_name)
        sp_args = {"bk_path": backup_path, "db_to_backup": self.name}
        keys_varchar = [backup_path, self.name]
        self.run_sp(sp_name="BK_DATABASE", sp_args=sp_args, keys_varchar=keys_varchar)
        logging.info("[%-10s]: creato backup database %s in %s", self.name, self.name, backup_path)

    # SELECTs
    def get_movements(self, get_all):
        movements = {}
        for id_mov, name_mov in self.mov_info.items():
            if get_all is True or "Saldo Debito - Credito" not in name_mov[0]:
                movements[id_mov] = name_mov[0]
        return movements

    def get_info_db(self, info_type):
        """Restituisce un dizionario sui tipi di pagamento nel formato {id_pagamento: nome_pagamento}"""
        _types = {"pagamenti": "MAP_PAGAMENTI", "spese_varie": "MAP_SPESE_VARIE", "entrate": "MAP_ENTRATE"}
        sql_string = self.format_sql_string(suide="S",
                                            table_name=_types[info_type],
                                            field_select_list=["ID", "DESCRIZIONE"],
                                            order_by_dict={"ID": "DESC"})
        self.exec_query_sql(sql_string)
        info_data = {}
        for row in self.cursor:
            info_data[int(row.ID)] = row.DESCRIZIONE
        return info_data

    def get_bi_credentials(self, role="ADMIN"):
        """Recupera username e password per accedere alla BI, parametro role per un ruolo diverso da ADMIN"""
        sql_string = self.format_sql_string(suide="S",
                                            table_name="QLIK_USERS",
                                            field_select_list=["username", "password"],
                                            where_dict={"RUOLO": role},
                                            keys_varchar=[role])
        try:
            logging.debug("[%-10s]: recupero credenziali BI - esecuzione della stringa SQL: %s", self.name, sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]: recupero credenziali BI - errore -  trace: %s", self.name, str(error))
            raise FatalError("Errore nel recupero delle credenziali della BI, consulta il log per maggiori dettagli")
        else:
            row = self.cursor.fetchone()
            if self.cursor.fetchone() is None:
                logging.debug("[%-10s]: recupero credenziali BI - esecuzione riuscita" % self.name)
                return row.username, row.password
            else:
                logging.error("[%-10s]: recupero credenziali BI - errore - trovato più di un record per il ruolo: %s", self.name, role)
                raise FatalError("Errore nel recupero delle credenziali della BI, consulta il log per maggiori dettagli")

    def get_password_from_username(self, username):
        """Resituisce la password (sha256) relativa all'utente dato in input"""
        sql_str = self.format_sql_string(suide="S",
                                         table_name="WALLET_USERS",
                                         field_select_list=["PASSWORD"],
                                         where_dict={"USERNAME": username},
                                         keys_varchar=[username])
        try:
            logging.debug("[%-10s]: recupero password da username - esecuzione della stringa SQL: %s", self.name, sql_str)
            self.cursor.execute(sql_str)
        except pyodbc.Error as error:
            logging.error("[%-10s]: recupero password da username - errore - trace: %s", self.name, str(error))
            raise FatalError("Errore nel login, consulta il log per maggiori dettagli")
        else:
            password = self.cursor.fetchval()
            if password is not None:
                logging.debug("[%-10s]: recupero password da username - esecuzione riuscita" % self.name)
                return password
            else:
                logging.debug("[%-10s]: recupero password da username - username non esistente" % self.name)
                return None

    def get_table_name_from_type_mov(self, type_movement):
        """A seconda del movimento passato restituisce il relativo nome della tabella"""
        sql_string = self.format_sql_string(suide="S",
                                            table_name="MAP_MOVIMENTI",
                                            field_select_list=["NOME_TABELLA"],
                                            where_dict={"DESCRIZIONE": type_movement},
                                            keys_varchar=[type_movement])
        try:
            logging.debug("[%-10s]: recupero nome tabella - esecuzione della stringa SQL: %s", self.name, sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]: recupero nome tabella - errore - trace: %s", self.name, str(error))
            raise FatalError("Errore nel recupero del nome della tabella del movimento {}, consulta il log per maggiori dettagli".format(type_movement))
        else:
            logging.debug("[%-10s]: recupero nome tabella - esecuzione riuscita" % self.name)
            return self.cursor.fetchval()

    def get_open_deb_creds(self):           # NB stessa di get_last_n_records()
        """Ottiene tutti i debiti-crediti non ancora saldati, leggendo dalla vista V_DEBITI_CREDITI_APERTI restituise
         una lista contente i nomi dei campi e una matrice di tutte le righe raccolte"""
        sql_string = self.format_sql_string(suide="S",
                                            table_name="V_DEBITI_CREDITI_APERTI",
                                            order_by_dict={"convert(date, DATA, 103)": "DESC"})
        try:
            logging.debug("[%-10s]: raccolta debiti/crediti aperti - esecuzione della stringa SQL: %s", self.name, sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]: raccolta debiti/crediti aperti - errore - trace: %s", self.name, str(error))
            raise FatalError("Errore nella raccolta dei debiti/crediti aperti, consulta il log per maggiori dettagli")
        else:
            logging.debug("[%-10s]: raccolta debiti/crediti aperti - esecuzione riuscita" % self.name)
            matrix_deb_cred = []            # matrice contenente i vari debiti/crediti aperti
            column_list = []                # lista dei nomi delle colonne

            for column in self.cursor.description:
                if column[0] != "ID":               # la colonna id mi serve come riferimento interno, il nome non mi interessa
                    column_list.append(column[0])

            for row in self.cursor:  # voglio inserire una lista, non un'istanza di Row, da qui la list comprehension
                matrix_deb_cred.append([elem for elem in row])
            return column_list, matrix_deb_cred

    def get_last_n_records(self, no_rows, type_movement):
        """Restituisce i primi n valori di una tabella e l'elenco dei campi che la compongono
        - no_rows -> numero di record da restituire
        - type_movement -> tipo di movimento, da cui si ricava il nome della tabella"""
        table_name = self.get_table_name_from_type_mov(type_movement)
        v_table_name = "V_{}".format(table_name)
        try:
            sql_string = self.format_sql_string(suide="S",
                                                table_name=v_table_name,
                                                top=no_rows,
                                                order_by_dict={"ID": "DESC"})
            logging.debug("[%-10s]: raccolta record movimenti - esecuzione della stringa SQL: %s", self.name, sql_string)
            self.cursor.execute(sql_string)
        except WrongValueInsert as error:  # ho inserito un valore non valido nella stringa (nello specifico il numero di record da visualizzare che viene dato grezzo in input) segnalo
            logging.error("[%-10s]: raccolta record movimenti - errore - trace: %s", self.name, str(error))
            raise WrongValueInsert(str(error))
        except pyodbc.Error as error:
            logging.error("[%-10s]: raccolta record movimenti - errore - trace: %s", self.name, str(error))
            raise FatalError(
                "Errore nella raccolta dei record del movimento tipo {}, consulta il log per maggiori dettagli".format(
                    type_movement))

        else:
            logging.debug("[%-10s]: raccolta record movimenti - esecuzione riuscita" % self.name)
            column_list = []  # lista dei nomi delle colonne
            matrix_mov = []  # matrice contenente i vari x movimenti di tipo y

            for column in self.cursor.description:
                if column[0] != "ID":  # la colonna id mi serve come riferimento interno, il nome non mi interessa
                    column_list.append(column[0])

            for row in self.cursor:  # voglio inserire una lista, non un'istanza di Row, da qui la list comprehension
                matrix_mov.append([elem for elem in row])
            return column_list, matrix_mov

    def drop_record(self, id_record):
        self.run_sp(sp_name="REMOVE_MOVEMENT", sp_args={"id_mov_to_drop": id_record})
        logging.info("[%-10s]: rimosso movimento id %s", self.name, id_record)

    def turn_deb_cred_into_mov(self, list_records):
        for id_record in list_records:
            self.run_sp(sp_name="TURN_INTO_MOVEMENT", sp_args={"id_record": id_record})
            logging.info("[%-10s]: convertito record id %s", self.name, id_record)

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
            - join_table -> tabella da joinare, NB per ora non sono previsti join multipli
            - join_fields -> dizionario di campi da uguagliare per il join
            - keys_varchar -> lista di valori varchar da inserire in select, where, insert o update, restituisce il valore nello statement SQL racchiuso da singoli apici
            - order_by_dict -> coppie CAMPO: DESC/ASC
            - top -> se diverso da None mostra le prime top (int) righe
            - sp_name -> nome procedura da eseguire
            - sp_args -> dizionario nella forma {nome_argomento: valore_argomento}"""
        sql_string = ""
        join_types_dict = {"I": "INNER JOIN", "L": "LEFT JOIN", "R": "RIGHT JOIN", "C": "CROSS JOIN"}

        if suide == 'S':
            sql_string = "SELECT * FROM {}".format(table_name)

            if top is not None:  # inserisco top x nella select
                if str(top).isdigit():
                    top_n_values = "top {}".format(int(top))
                    sql_string = sql_string.replace("SELECT", "SELECT {}".format(top_n_values))

                else:
                    raise WrongValueInsert(
                        "Non è stato passato un valore numerico per il numero di record da selezionare")

            if isinstance(field_select_list, list):  # field_select_list <> None rimuovo '*' e creo l'elenco dei campi
                fields_to_select = ", ".join(field_select_list)
                sql_string = sql_string.replace("*", fields_to_select)

            elif where_dict:
                raise WrongValueInsert(
                    "è stato passato un parametro non valido per la condizione SELECT, deve essere list")

            if join_dict or join_table or join_type:
                if join_type in join_types_dict and join_table and isinstance(join_dict,
                                                                              dict):  # in questo caso devo inserire anche un join
                    fields_to_join = " AND ".join("{} = {}".format(key, value) for key, value in join_dict.items())
                    sql_string = " ".join(
                        [sql_string, join_types_dict.get(join_type), join_table, "ON", fields_to_join])

                else:
                    raise WrongValueInsert(
                        "Nel caso di un join deve essere fornita sia la tabella da legare, sia l'elenco "
                        "dei cambi da uguagliare, sia il parametro corretto per il tipo di join")

            if isinstance(where_dict, dict):  # se where_dict <> da None aggiungo anche le restrizioni tramite WHERE statement
                fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else value) for
                                                key, value in
                                                where_dict.items())
                sql_string = " ".join([sql_string, "WHERE", fields_to_filter])

            elif where_dict:
                raise WrongValueInsert(
                    "è stato passato un parametro non valido per la condizione WHERE, deve essere dict")

            if isinstance(order_by_dict, dict):  # se order_by_dict <> da None inserisco l'ordinamento
                fields_to_order_by = ", ".join("{} {}".format(key, value) for key, value in order_by_dict.items())
                sql_string = " ".join([sql_string, "ORDER BY", fields_to_order_by])

            elif order_by_dict:
                raise WrongValueInsert(
                    "è stato passato un parametro non valido per la condizione ORDER BY, deve essere dict")
        elif suide == 'U':
            sql_string = "UPDATE {} SET".format(table_name)

            if isinstance(update_dict, dict):
                fields_to_update = ", ".join("{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else value) for
                                             key, value in
                                             update_dict.items())
                sql_string = " ".join([sql_string, fields_to_update])

            else:
                raise WrongValueInsert(
                    "Non è stata fornita la lista dei campi da modificare oppure il tipo non è corretto, deve essere dict")

            if isinstance(where_dict,
                          dict):  # se where_dict è tipo dict aggiungo anche le restrizioni tramite WHERE statement
                fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else value) for
                                                key, value in
                                                where_dict.items())
                sql_string = " ".join([sql_string, "WHERE", fields_to_filter])

            elif where_dict is not None:
                raise WrongValueInsert(
                    "è stato passato un parametro non valido per la condizione WHERE, deve essere dict")

            else:  # cautela personale per non modificare una tabella per intero
                raise WrongValueInsert("Non si può modificare interamente una tabella!")
        elif suide == 'I':
            if isinstance(insert_dict,
                          dict):  # mi accerto che venga fornita la lista dei campi e il loro relativo valore da aggiungere
                sql_string = "INSERT INTO {}".format(table_name)
                fields_to_insert = "({})".format(", ".join(insert_dict.keys()))  # elenco campi da inserire
                values_to_insert = "({})".format(", ".join(["'{}'".format(
                    Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else str(value) for
                                                            value in
                                                            insert_dict.values()]))  # elenco valori da inserire

                sql_string = " ".join([sql_string, fields_to_insert, "VALUES", values_to_insert])

            elif insert_dict is not None:
                raise WrongValueInsert(
                    "è stato passato un parametro non valido per la condizione INSERT, deve essere dict")

            else:
                raise WrongValueInsert("Non è stata fornita la lista dei campi da inserire!")
        elif suide == 'D':
            sql_string = "DELETE {}".format(table_name)

            if isinstance(where_dict,
                          dict):  # non voglio mai cancellare per intero la tabella, faccio sì che debbano esserci sempre clausole WHERE
                fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if keys_varchar and value in keys_varchar else value) for
                                                key, value in
                                                where_dict.items())
                sql_string = " ".join([sql_string, "WHERE", fields_to_filter])

            elif where_dict is not None:
                raise WrongValueInsert(
                    "è stato passato un parametro non valido per la condizione WHERE, deve essere dict")

            else:
                raise WrongValueInsert("Non è possibile eliminare per intero una tabella!")
        elif suide == "E":
            sql_string = "exec {} ".format(sp_name)
            if sp_args is not None:
                str_args = []
                for arg_name, arg_value in sp_args.items():
                    if keys_varchar and arg_name in keys_varchar:
                        str_args.append("@{} = '{}'".format(arg_name, Tools.escape_sql_chars(arg_value)))
                    else:
                        str_args.append("@{} = {}".format(arg_name, arg_value))
                sql_string = sql_string + ", ".join(str_args)
        return sql_string


if __name__ == "__main__":
    pass



