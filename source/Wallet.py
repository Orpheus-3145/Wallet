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
        logging.info("[%-10s]: %s", "Wallet", "*" * 80)
        try:
            self._dsn = dsn
            self.connection = pyodbc.connect(self._dsn, autocommit=True)
            self.cursor = self.connection.cursor()
        except pyodbc.Error as error:
            logging.error("[%-10s]: avvio istanza - errore - trace: %s", "Wallet", str(error))
            raise FatalError("Errore nella connessione al database, consulta il log per maggiori dettagli")
        else:
            logging.info("[%-10s]: avvio istanza - creazione di un'istanza di Wallet e connessione al database riuscita" % "Wallet")

    def login_wallet(self, username, password):
        """Tenta il login con user e pwd"""
        hash_pwd_db = self.get_password_from_username(username)
        if hash_pwd_db is None:
            return False
        hash_pwd_input = sha256(str(password).encode()).hexdigest()

        if hash_pwd_input == hash_pwd_db:  # pwd corretta
            logging.info("[%-10s]: login nell'app - password corretta, login effettuato" % "Wallet")
            return True

        else:
            logging.debug("[%-10s]: login nell'app - password non corretta, login fallito" % "Wallet")
            return False

    def insert_movement(self, type_mov, data_info):
        if "str_data_mov" in data_info:
            self.check_date(data_info["str_data_mov"])
        if type_mov == "Spesa Generica":
            self.insert_spesa_varia(data_info)
        elif type_mov == "Spesa Fissa":
            self.insert_spesa_fissa(data_info)
        elif type_mov == "Stipendio":
            self.insert_stipendio(data_info)
        elif type_mov == "Entrata":
            self.insert_entrata(data_info)
        elif type_mov == "Debito - Credito":
            self.insert_deb_cred(data_info)
        elif type_mov == "Saldo Debito - Credito":
            self.insert_saldo_deb_cred(data_info)
        elif type_mov == "Spesa di Mantenimento":
            self.insert_spesa_mantenimento(data_info)
        elif type_mov == "Spesa di Viaggio":
            self.insert_spesa_viaggio(data_info)
        time.sleep(0.1)  # metto in pausa per 0.1 secondi per evitare che la (bassa) precisione di DATETIME di SQL scriva valori uguali

    def insert_spesa_varia(self, data_info):
        if "importo" not in data_info:
            raise WrongValueInsert("Importo mancante")
        self.check_float(data_info["importo"])
        if "type_pag" not in data_info:
            raise WrongValueInsert("Tipo di pagamento mancante")
        elif "descrizione" not in data_info or data_info["descrizione"].strip() == "":
            raise WrongValueInsert("Descrizione non inserita")
        varchar_values = []
        if "str_data_mov" in data_info:
            varchar_values.append(data_info["str_data_mov"])
        varchar_values.append(data_info["type_pag"])
        if "note" in data_info:
            varchar_values.append(data_info["note"])
        varchar_values.append(data_info["type_s_varia"])
        varchar_values.append(data_info["descrizione"])
        self.run_sp(sp_name="INSERISCI_S_VARIA", sp_args=data_info, varchar_values=varchar_values)

    def insert_spesa_fissa(self, data_info):
        if "importo" not in data_info:
            raise WrongValueInsert("Importo mancante")
        self.check_float(data_info["importo"])
        if "type_pag" not in data_info:
            raise WrongValueInsert("Tipo di pagamento mancante")
        elif "descrizione" not in data_info or data_info["descrizione"].strip() == "":
            raise WrongValueInsert("Descrizione mancante")
        varchar_values = []
        if "str_data_mov" in data_info:
            varchar_values.append(data_info["str_data_mov"])
        varchar_values.append(data_info["type_pag"])
        if "note" in data_info:
            varchar_values.append(data_info["note"])
        varchar_values.append(data_info["descrizione"])
        self.run_sp(sp_name="INSERISCI_S_FISSA", sp_args=data_info, varchar_values=varchar_values)

    def insert_stipendio(self, data_info):
        if "importo" not in data_info:
            raise WrongValueInsert("Importo mancante")
        elif "type_pag" not in data_info:
            raise WrongValueInsert("Tipo di pagamento mancante")
        elif "ddl" not in data_info or data_info["ddl"].strip() == "":
            raise WrongValueInsert("DDL non inserito")
        for type_t in ["importo", "netto", "rimborso_spese"]:
            if type_t in data_info:
                self.check_float(data_info[type_t])
        varchar_values = []
        if "str_data_mov" in data_info:
            varchar_values.append(data_info["str_data_mov"])
        varchar_values.append(data_info["type_pag"])
        if "note" in data_info:
            varchar_values.append(data_info["note"])
        varchar_values.append(data_info["ddl"])
        self.run_sp(sp_name="INSERISCI_STIPENDIO", sp_args=data_info, varchar_values=varchar_values)

    def insert_entrata(self, data_info):
        if "importo" not in data_info:
            raise WrongValueInsert("Importo mancante")
        self.check_float(data_info["importo"])
        if "type_pag" not in data_info:
            raise WrongValueInsert("Tipo di pagamento mancante")
        elif "type_entrata" not in data_info:
            raise WrongValueInsert("Tipo di entrata mancante")
        elif "descrizione" not in data_info or data_info.get("descrizione").strip() == "":
            raise WrongValueInsert("Descrizione mancante")
        varchar_values = []
        if "str_data_mov" in data_info:
            varchar_values.append(data_info["str_data_mov"])
        varchar_values.append(data_info["type_pag"])
        if "note" in data_info:
            varchar_values.append(data_info["note"])
        varchar_values.append(data_info["type_entrata"])
        varchar_values.append(data_info["descrizione"])
        self.run_sp(sp_name="INSERISCI_ENTRATA", sp_args=data_info, varchar_values=varchar_values)

    def insert_deb_cred(self, data_info):
        if "importo" not in data_info:
            raise WrongValueInsert("Importo mancante")
        self.check_float(data_info["importo"])
        if "type_pag" not in data_info:
            raise WrongValueInsert("Tipo di pagamento mancante")
        elif "deb_cred" not in data_info:
            raise WrongValueInsert("Specificare debito o credito")
        elif "origine" not in data_info or data_info["origine"].strip() == "":
            raise WrongValueInsert("Origine non inserita")
        elif "descrizione" not in data_info or data_info["descrizione"].strip() == "":
            raise WrongValueInsert("Descrizione non inserita")
        varchar_values = []
        if "str_data_mov" in data_info:
            varchar_values.append(data_info["str_data_mov"])
        varchar_values.append(data_info["type_pag"])
        if "note" in data_info:
            varchar_values.append(data_info["note"])
        varchar_values.append(data_info["origine"])
        varchar_values.append(data_info["descrizione"])
        self.run_sp(sp_name="INSERISCI_DEB_CRED", sp_args=data_info, varchar_values=varchar_values)

    def insert_saldo_deb_cred(self, data_info):
        if "importo" in data_info:
            self.check_float(data_info["importo"])
        if "type_pag" not in data_info:
            raise WrongValueInsert("Tipo di pagamento mancante")
        elif "id_saldo_deb_cred" not in data_info:
            raise WrongValueInsert("Nessun entità selezionata")
        varchar_values = []
        if "str_data_mov" in data_info:
            varchar_values.append(data_info["str_data_mov"])
        varchar_values.append(data_info["type_pag"])
        if "note" in data_info:
            varchar_values.append(data_info["note"])
        varchar_values.append(data_info["id_saldo_deb_cred"])
        self.run_sp(sp_name="SALDA_DEB_CRED", sp_args=data_info, varchar_values=varchar_values)

    def insert_spesa_mantenimento(self, data_info):
        if "importo" not in data_info:
            raise WrongValueInsert("Importo mancante")
        self.check_float(data_info["importo"])
        if "type_pag" not in data_info:
            raise WrongValueInsert("Tipo di pagamento mancante")
        elif "descrizione" not in data_info or data_info["descrizione"].strip() == "":
            raise WrongValueInsert("Descrizione non inserita")
        varchar_values = []
        if "str_data_mov" in data_info:
            varchar_values.append(data_info["str_data_mov"])
        varchar_values.append(data_info["type_pag"])
        if "note" in data_info:
            varchar_values.append(data_info["note"])
        varchar_values.append(data_info["descrizione"])
        self.run_sp(sp_name="INSERISCI_S_VARIA", sp_args=data_info, varchar_values=varchar_values)

    def insert_spesa_viaggio(self, data_info):
        if "importo" not in data_info:
            raise WrongValueInsert("Importo mancante")
        self.check_float(data_info["importo"])
        if "type_pag" not in data_info:
            raise WrongValueInsert("Tipo di pagamento mancante")
        elif "descrizione" not in data_info or data_info["descrizione"].strip() == "":
            raise WrongValueInsert("Descrizione non inserita")
        elif "viaggio" not in data_info or data_info.get("viaggio").strip() == "":
            raise WrongValueInsert("Viaggio mancante")
        varchar_values = []
        if "str_data_mov" in data_info:
            varchar_values.append(data_info["str_data_mov"])
        varchar_values.append(data_info["type_pag"])
        if "note" in data_info:
            varchar_values.append(data_info["note"])
        varchar_values.append(data_info["viaggio"])
        varchar_values.append(data_info["descrizione"])
        self.run_sp(sp_name="INSERISCI_S_VIAGGIO", sp_args=data_info, varchar_values=varchar_values)

    def check_date(self, input_date):
        """Verifica che il dizionario in input contenga una data e la restituisce come istanza di datetime"""
        try:
            datetime.strptime(input_date, "%d/%m/%Y")
        except (KeyError, ValueError):
            raise WrongValueInsert("Data non valida")

    def check_float(self, number):
        try:
            number = Tools.convert_to_float(number)
            if number <= 0:
                raise WrongValueInsert("Importo nullo o negativo")
        except (TypeError, ValueError):
            raise WrongValueInsert("Importo non valido")

    def run_sp(self, sp_name, sp_args=None, varchar_values=None):
        if sp_args is None:
            sp_args = []
        if varchar_values is None:
            varchar_values = []
        sp_exec = self.format_sql_string(suide="E",
                                         sp_name=sp_name,
                                         proc_args_dict=sp_args,
                                         varchar_values=varchar_values)
        print(sp_exec)
        try:
            logging.debug("[%-10s]: esecuzione della query: %s", "Wallet", sp_exec)
            self.cursor.execute(sp_exec)
        except pyodbc.Error as err:
            logging.error("[%-10s]: errore - trace: %s", "Wallet", str(err))
            raise FatalError("Errore nel database, consulta il log per maggiori dettagli")
        else:
            logging.debug("[%-10s]: esecuzione riuscita", "Wallet")

    def close_wallet(self):
        """concludo il log"""
        self.cursor.close()
        self.connection.close()
        logging.info("[%-10s]: chiusura di wallet e del collegamento al database... " % "Wallet")
        logging.info("[%-10s]: %s", "Wallet", "*" * 80)

    def backup_database(self, db_name, backup_path):
        backup_name = "{}_{}.bak".format(db_name, datetime.now().strftime("%d-%m-%Y"))
        if not os.path.isabs(backup_path):
            backup_path = os.path.normpath(os.path.join(os.getcwd(), backup_path))
        count = 1
        while os.path.exists(os.path.join(backup_path, backup_name)):
            backup_name = "{}_{}_{}.bak".format(db_name, datetime.now().strftime("%d-%m-%Y"), count)
            count += 1
        backup_path = os.path.join(backup_path, backup_name)
        sp_args = {"bk_path": backup_path, "db_to_backup": db_name}
        varchar_values = [backup_path, db_name]
        self.run_sp(sp_name="BK_DATABASE", sp_args=sp_args, varchar_values=varchar_values)
        logging.info("[%-10s]: creato backup database %s in %s", "Wallet", db_name, backup_path)

    def get_open_deb_creds(self):
        """Ottiene tutti i debiti-crediti non ancora saldati, leggendo dalla vista V_DEBITI_CREDITI_APERTI restituise
         una lista contente i nomi dei campi e una matrice di tutte le righe raccolte"""
        sql_string = self.format_sql_string(suide="S",
                                            table_name="V_DEBITI_CREDITI_APERTI",
                                            order_by_dict={"convert(date, DATA, 103)": "DESC"})
        try:
            logging.debug("[%-10s]: raccolta debiti/crediti aperti - esecuzione della stringa SQL: %s", "Wallet", sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]: raccolta debiti/crediti aperti - errore - trace: %s", "Wallet", str(error))
            raise FatalError("Errore nella raccolta dei debiti/crediti aperti, consulta il log per maggiori dettagli")
        else:
            logging.debug("[%-10s]: raccolta debiti/crediti aperti - esecuzione riuscita" % "Wallet")
            matrix_deb_cred = []            # matrice contenente i vari debiti/crediti aperti
            column_list = []                # lista dei nomi delle colonne

            for column in self.cursor.description:
                if column[0] != "ID":               # la colonna id mi serve come riferimento interno, il nome non mi interessa
                    column_list.append(column[0])

            for row in self.cursor:  # voglio inserire una lista, non un'istanza di Row, da qui la list comprehension
                matrix_deb_cred.append([elem for elem in row])
            return column_list, matrix_deb_cred

    def get_movements(self, type_mov=None, name_mov=None):
        partial_sql = partial(self.format_sql_string,
                              suide="S",
                              table_name="MAP_MOVIMENTI",
                              field_select_list=["DESCRIZIONE"],
                              order_by_dict={"DESCRIZIONE": "ASC"})
        if type_mov:    # filtro nel caso cerchi il tipo di movimento (deb/cred o general)
            sql_string = partial_sql(where_dict={"TIPO_MOVIMENTO": type_mov}, varchar_values=[type_mov])
        elif name_mov:  # oppure il nome preciso
            sql_string = partial_sql(where_dict={"DESCRIZIONE": name_mov}, varchar_values=[name_mov])
        else:           # oppure per tutti i movimenti
            sql_string = partial_sql()
        try:
            logging.debug("[%-10s]: raccolta tipi di movimenti - esecuzione della stringa SQL: %s", "Wallet", sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]: raccolta tipi di movimenti - errore - trace: %s", "Wallet", str(error))
            raise FatalError("Errore nella raccolta dei tipi di movimenti, consulta il log per maggiori dettagli")
        else:
            movement_list = []
            for row in self.cursor:
                movement_list.append(row.DESCRIZIONE)
            logging.debug("[%-10s]: raccolta tipi di movimenti - esecuzione riuscita, valori trovati - %s", "Wallet",
                          Tools.list_to_str(movement_list))
            return movement_list

    def get_info_db(self, info_type):
        """Restituisce un dizionario sui tipi di pagamento nel formato {id_pagamento: nome_pagamento}"""
        _types = {"pagamenti": "MAP_PAGAMENTI", "spese_varie": "MAP_SPESE_VARIE", "entrate": "MAP_ENTRATE"}
        try:
            sql_string = self.format_sql_string(suide="S",
                                                table_name=_types[info_type],
                                                field_select_list=["DESCRIZIONE"],
                                                order_by_dict={"DESCRIZIONE": "ASC"})
            logging.debug("[%-10s]: raccolta tipi di %s - esecuzione della stringa SQL: %s", "Wallet", info_type, sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]:  raccolta tipi di %s - errore - trace: {}", "Wallet", info_type, str(error))
            raise FatalError("Errore database, consulta il log per maggiori dettagli")
        except ValueError:
            logging.error("[%-10s]:  errore - chiave sconosciuta: %s", "Wallet", info_type)
            raise FatalError("Errore interno, consulta il log per maggiori dettagli")
        else:
            info_data = []
            for row in self.cursor:
                info_data.append(row.DESCRIZIONE)
            logging.debug("[%-10s]: raccolta tipi di %s - esecuzione riuscita", "Wallet", info_type)
            return info_data

    def get_bi_credentials(self, role="ADMIN"):
        """Recupera username e password per accedere alla BI, parametro role per un ruolo diverso da ADMIN"""
        sql_string = self.format_sql_string(suide="S",
                                            table_name="QLIK_USERS",
                                            field_select_list=["username", "password"],
                                            where_dict={"RUOLO": role},
                                            varchar_values=[role])
        try:
            logging.debug("[%-10s]: recupero credenziali BI - esecuzione della stringa SQL: %s", "Wallet", sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]: recupero credenziali BI - errore -  trace: %s", "Wallet", str(error))
            raise FatalError("Errore nel recupero delle credenziali della BI, consulta il log per maggiori dettagli")
        else:
            row = self.cursor.fetchone()
            if self.cursor.fetchone() is None:
                logging.debug("[%-10s]: recupero credenziali BI - esecuzione riuscita" % "Wallet")
                return row.username, row.password
            else:
                logging.error("[%-10s]: recupero credenziali BI - errore - trovato più di un record per il ruolo: %s", "Wallet", role)
                raise FatalError("Errore nel recupero delle credenziali della BI, consulta il log per maggiori dettagli")

    def get_password_from_username(self, username):
        """Resituisce la password (sha256) relativa all'utente dato in input"""
        sql_str = self.format_sql_string(suide="S",
                                         table_name="WALLET_USERS",
                                         field_select_list=["PASSWORD"],
                                         where_dict={"USERNAME": username},
                                         varchar_values=[username])
        try:
            logging.debug("[%-10s]: recupero password da username - esecuzione della stringa SQL: %s", "Wallet", sql_str)
            self.cursor.execute(sql_str)
        except pyodbc.Error as error:
            logging.error("[%-10s]: recupero password da username - errore - trace: %s", "Wallet", str(error))
            raise FatalError("Errore nel login, consulta il log per maggiori dettagli")
        else:
            password = self.cursor.fetchval()
            if password is not None:
                logging.debug("[%-10s]: recupero password da username - esecuzione riuscita" % "Wallet")
                return password
            else:
                logging.debug("[%-10s]: recupero password da username - username non esistente" % "Wallet")
                return None

    def get_table_name_from_type_mov(self, type_movement):
        """A seconda del movimento passato restituisce il relativo nome della tabella"""
        sql_string = self.format_sql_string(suide="S",
                                            table_name="MAP_MOVIMENTI",
                                            field_select_list=["NOME_TABELLA"],
                                            where_dict={"DESCRIZIONE": type_movement},
                                            varchar_values=[type_movement])
        try:
            logging.debug("[%-10s]: recupero nome tabella - esecuzione della stringa SQL: %s", "Wallet", sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]: recupero nome tabella - errore - trace: %s", "Wallet", str(error))
            raise FatalError("Errore nel recupero del nome della tabella del movimento {}, consulta il log per maggiori dettagli".format(type_movement))
        else:
            logging.debug("[%-10s]: recupero nome tabella - esecuzione riuscita" % "Wallet")
            return self.cursor.fetchval()

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
                                                order_by_dict={"convert(date, DATA, 103)": "DESC"})
            logging.debug("[%-10s]: raccolta record movimenti - esecuzione della stringa SQL: %s", "Wallet", sql_string)
            self.cursor.execute(sql_string)
        except WrongValueInsert as error:  # ho inserito un valore non valido nella stringa (nello specifico il numero di record da visualizzare che viene dato grezzo in input) segnalo
            logging.error("[%-10s]: raccolta record movimenti - errore - trace: %s", "Wallet", str(error))
            raise WrongValueInsert(str(error))
        except pyodbc.Error as error:
            logging.error("[%-10s]: raccolta record movimenti - errore - trace: %s", "Wallet", str(error))
            raise FatalError(
                "Errore nella raccolta dei record del movimento tipo {}, consulta il log per maggiori dettagli".format(
                    type_movement))

        else:
            logging.debug("[%-10s]: raccolta record movimenti - esecuzione riuscita" % "Wallet")
            column_list = []  # lista dei nomi delle colonne
            matrix_mov = []  # matrice contenente i vari x movimenti di tipo y

            for column in self.cursor.description:
                if column[0] != "ID":  # la colonna id mi serve come riferimento interno, il nome non mi interessa
                    column_list.append(column[0])

            for row in self.cursor:  # voglio inserire una lista, non un'istanza di Row, da qui la list comprehension
                matrix_mov.append([elem for elem in row])
            return column_list, matrix_mov

    def drop_records(self, list_records, type_movement):
        """Riceve una lista di ID (appartenenti alla tabella movimenti) cancella la relativa riga della tabella generica
        movimenti, e specifica tramite il campo ID_MOV"""
        if not list_records:
            raise WrongValueInsert("Non è stato selezionato nessun record")

        for record in list_records:
            sql_string_delete_spec = self.format_sql_string(suide="D",
                                                            table_name=self.get_table_name_from_type_mov(type_movement),
                                                            where_dict={"ID_MOV": record})
            sql_string_delete_main = self.format_sql_string(suide="D",
                                                            table_name="MOVIMENTI",
                                                            where_dict={"ID": record})
            try:
                self.cursor.execute(sql_string_delete_spec)
                logging.debug("[%-10s]: eliminazione movimento id: %s - esecuzione della stringa SQL: %s", "Wallet", record, sql_string_delete_spec)
                self.cursor.execute(sql_string_delete_main)
                logging.debug("[%-10s]: eliminazione movimento id: %s - esecuzione della stringa SQL: %s", "Wallet", record, sql_string_delete_main)

            except pyodbc.Error as error:
                logging.error("[%-10s]: eliminazione movimento id: %s - errore - trace: %s", "Wallet", record, str(error))
                self.cursor.rollback()
                raise FatalError("Errore nella rimozione del movimento id: {}, consulta il log per maggiori dettagli".format(record))

            else:
                logging.info("[%-10s]: eliminazione movimento id: %s - movimento rimosso", "Wallet", record)

        self.cursor.commit()

    def turn_deb_cred_into_mov(self, list_records):
        """Riceve una lista di ID (appartenenti alla tabella movimenti) cancella la relativa riga della tabella generica
        movimenti, e specifica tramite il campo ID_MOV"""
        if not list_records:
            raise WrongValueInsert("Non è stato selezionato nessun record")
        for id_record in list_records:
            sql_string = self.format_sql_string(suide="E",
                                                sp_name="TURN_INTO_MOVEMENT",
                                                proc_args_dict={"id_record": id_record})
            try:
                logging.debug("[%-10s]: conversione deb/cred id: %s- esecuzione della stringa SQL: %s", "Wallet", id_record, sql_string)
                self.cursor.execute(sql_string)
            except pyodbc.Error as error:
                logging.error("[%-10s]: conversione deb/cred id: %s - errore - trace: %s", "Wallet", id_record, str(error))
                raise FatalError("Errore nella conversione, consulta il log per maggiori dettagli")
            else:
                logging.info("[%-10s]: conversione deb/cred id: %s - record convertito ", "Wallet", id_record)

    def format_sql_string(self, suide,
                          table_name=None,
                          field_select_list=None,
                          where_dict=None,
                          update_dict=None,
                          insert_dict=None,
                          join_type=None,
                          join_table=None,
                          join_dict=None,
                          varchar_values=None,
                          order_by_dict=None,
                          top=None,
                          sp_name=None,
                          proc_args_dict=None):
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
            - varchar_values -> lista di valori varchar da inserire in select, where, insert o update, restituisce il valore nello statement SQL racchiuso da singoli apici
            - order_by_dict -> coppie CAMPO: DESC/ASC
            - top -> se diverso da None mostra le prime top (int) righe
            - sp_name -> nome procedura da eseguire
            - proc_args_dict -> dizionario nella forma {nome_argomento: valore_argomento}"""
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

            if isinstance(where_dict,
                          dict):  # se where_dict <> da None aggiungo anche le restrizioni tramite WHERE statement
                fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for
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
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for
                                             key, value in
                                             update_dict.items())
                sql_string = " ".join([sql_string, fields_to_update])

            else:
                raise WrongValueInsert(
                    "Non è stata fornita la lista dei campi da modificare oppure il tipo non è corretto, deve essere dict")

            if isinstance(where_dict,
                          dict):  # se where_dict è tipo dict aggiungo anche le restrizioni tramite WHERE statement
                fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for
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
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else str(value) for
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
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for
                                                key, value in
                                                where_dict.items())
                sql_string = " ".join([sql_string, "WHERE", fields_to_filter])

            elif where_dict is not None:
                raise WrongValueInsert(
                    "è stato passato un parametro non valido per la condizione WHERE, deve essere dict")

            else:
                raise WrongValueInsert("Non è possibile eliminare per intero una tabella!")
        elif suide == "E":
            sql_string = "exec {}".format(sp_name)
            if isinstance(proc_args_dict, dict):  # se proc_args_dict <> da None aggiungo anche la lista di argomenti
                args = ", ".join("@{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for
                                 key, value in
                                 proc_args_dict.items())
                sql_string = " ".join([sql_string, args])
        return sql_string


if __name__ == "__main__":
    pass



