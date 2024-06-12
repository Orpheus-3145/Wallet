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
            self._dsn = dsn     # la tengo nel caso mi serva nel metodo backup_database()
            self.connection = pyodbc.connect(self._dsn, autocommit=True)
            self.cursor = self.connection.cursor()  # per comunicare con il database

        except pyodbc.Error as error:
            logging.error("[%-10s]: avvio istanza - errore - trace: %s", "Wallet", str(error))
            raise FatalError("Errore nella connessione al database, consulta il log per maggiori dettagli")

        else:
            logging.info("[%-10s]: avvio istanza - creazione di un'istanza di Wallet e connessione al database riuscita" % "Wallet")
            self._ready_to_insert_data = False          # proprietà valorizzata dal metodo check_values, indica se il movimento è stato controllato
            self.type_movement = ""                     # tipo di movimento da inserire
            self.data_movimento = ""                    # data del movimento
            self.main_mov_dict = {}                     # dati in input del movimento principale
            self.spec_mov_dict = {}                     # dati in input del movimento specifico

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

    def check_values(self, type_movement, date_mov, main_mov_dict, spec_mov_dict):
        """Riceve tutti i dati che non possono essere generati automaticamente (progressivi, date, ... ) e li verifica.
           Ogni movimento di spesa si compone di alcune informazioni comuni (importo, data, ... ) e altre specifiche al
           tipo di movimento:
               - type_movement: tipo di movimento di spesa, per i valori ammessi vedi config.MOV_LIST'
               - date_mov: data esecuzione movimento
               - main_mov_dict: dizionario contenete in valori in input da inserire nel mov. principale
               - spec_mov_dict: dizionario contenete in valori in input da inserire nel mov. specifico"""

        if self._ready_to_insert_data is True:
            raise FatalError("Movimento già verificato")

        logging.info("[%-10s]: verifica movimento - tipo di movimento: %s", "Wallet", type_movement)
        self.type_movement = type_movement

        # check sul movimento principale (main_mov_dict)
        if type_movement not in ["Stipendio", "Saldo Debito - Credito"]:  # se inserisco uno stipendio o un saldo d/c il movimento principale viene gestito in automatico
            if "IMPORTO" not in main_mov_dict.keys():
                raise WrongValueInsert("Importo non inserito")

            else:
                try:    # verifico l'importo
                    main_mov_dict["IMPORTO"] = Tools.replace_coma(main_mov_dict["IMPORTO"], return_type=float)  # sostituisco virgole con punti nell'importo
                    pow(main_mov_dict["IMPORTO"], -1)

                except (TypeError, ValueError, ZeroDivisionError):  # verifico che sia != None, un numero e diverso da 0
                    raise WrongValueInsert("Importo non valido")

            if "ID_PAG" not in main_mov_dict.keys():     # se non è presente nelle chiavi del dizionario allora non è stato inserito il tipo di pagamento
                raise WrongValueInsert("Tipo di pagamento non inserito")

            if "NOTE" not in main_mov_dict.keys():  # se non ci sono note lo valorizzo come vuoto
                main_mov_dict["NOTE"] = ""

            logging.info("[%-10s]: verifica movimento - informazioni principali corrette: %s", "Wallet",
                         Tools.list_to_str(main_mov_dict))

        id_type_movement = Tools.get_key_from_dict(self.get_movements(name_mov=self.type_movement), self.type_movement)
        main_mov_dict["TIPO_MOV"] = id_type_movement

        # check sul movimento di dettaglio (spec_mov_dict)
        if type_movement == "Spesa Generica":
            if "ID_TIPO_SPESA" not in spec_mov_dict.keys():
                raise WrongValueInsert("Tipo di spesa non inserito")

            if "DESCRIZIONE" not in spec_mov_dict.keys():  # se non c'è descrizione la valorizzo come vuota
                spec_mov_dict["DESCRIZIONE"] = ""
            main_mov_dict["DARE_AVERE"] = 0  # è una spesa, valorizzo dare

        elif type_movement == "Spesa Fissa":
            if "DESCRIZIONE" not in spec_mov_dict.keys() or spec_mov_dict["DESCRIZIONE"].strip == "":
                raise WrongValueInsert("Descrizione non inserita")
            main_mov_dict["DARE_AVERE"] = 0  # è una spesa, valorizzo dare

        elif type_movement == "Stipendio":
            if "PROVENIENZA" not in spec_mov_dict.keys() or spec_mov_dict["PROVENIENZA"].strip() == "":
                raise WrongValueInsert("DDL non inserito")

            if "TOTALE" not in spec_mov_dict.keys() or spec_mov_dict["TOTALE"].strip() == "":
                raise WrongValueInsert("Totale non inserito")
            else:
                try:
                    spec_mov_dict["TOTALE"] = Tools.replace_coma(spec_mov_dict["TOTALE"], return_type=float)
                    pow(spec_mov_dict["TOTALE"], -1)
                except (TypeError, ValueError, ZeroDivisionError):  # verifico che sia un numero, valido, e diverso da 0
                    raise WrongValueInsert("Totale non valido")

            if "NETTO" not in spec_mov_dict.keys() or spec_mov_dict["NETTO"].strip() == "":
                spec_mov_dict["NETTO"] = spec_mov_dict["TOTALE"]
            else:
                if spec_mov_dict["NETTO"].isnumeric() is False:  # verifico che sia un numero
                    raise WrongValueInsert("Netto non valido")
                else:
                    spec_mov_dict["NETTO"] = Tools.replace_coma(spec_mov_dict["NETTO"], return_type=float)

            if "RIMBORSO_SPESE" not in spec_mov_dict.keys() or spec_mov_dict["RIMBORSO_SPESE"].strip() == "":
                spec_mov_dict["RIMBORSO_SPESE"] = "0"
            else:
                if spec_mov_dict["RIMBORSO_SPESE"].isnumeric() is False:    # verifico che sia un numero
                    raise WrongValueInsert("Rimborso spese non valido")
                else:
                    spec_mov_dict["RIMBORSO_SPESE"] = Tools.replace_coma(spec_mov_dict["RIMBORSO_SPESE"], return_type=float)

            if "NOTE" not in spec_mov_dict.keys() or spec_mov_dict["NOTE"].strip() == "":  # se non ci sono le note valorizzo come vuoto
                spec_mov_dict["NOTE"] = ""
                main_mov_dict["NOTE"] = ""
            else:
                main_mov_dict["NOTE"] = spec_mov_dict["NOTE"]

            spec_mov_dict["TRATTENUTE"] = float(spec_mov_dict["TOTALE"]) - float(spec_mov_dict["NETTO"]) - float(spec_mov_dict["RIMBORSO_SPESE"])
            if int(spec_mov_dict["TRATTENUTE"]) < 0:
                raise WrongValueInsert("Inserito netto maggiore del totale")

            main_mov_dict["IMPORTO"] = spec_mov_dict["NETTO"]
            main_mov_dict["DARE_AVERE"] = 1     # è un'entrata, valorizzo avere
            main_mov_dict["ID_PAG"] = 5         # gli stipendi si accreditano mediante bonifico (id_payment: 5)

        elif type_movement == "Entrata":
            if "ID_TIPO_ENTRATA" not in spec_mov_dict.keys():
                raise WrongValueInsert("Tipo di entrata non inserito")
            if "DESCRIZIONE" not in spec_mov_dict.keys() or spec_mov_dict.get("DESCRIZIONE").strip() == "":
                raise WrongValueInsert("Descrizione non inserita")
            main_mov_dict["DARE_AVERE"] = 1  # è un'entrata, valorizzo avere

        elif type_movement == "Debito - Credito":
            if "ORIGINE" not in spec_mov_dict.keys() or spec_mov_dict.get("ORIGINE").strip() == "":
                raise WrongValueInsert("Origine non inserita")
            if "DESCRIZIONE" not in spec_mov_dict.keys() or spec_mov_dict.get("DESCRIZIONE").strip() == "":
                raise WrongValueInsert("Descrizione non inserita")
            if "DEBCRED" not in spec_mov_dict.keys():
                raise WrongValueInsert("Specificare debito o credito")
            main_mov_dict["DARE_AVERE"] = int(not bool(int(spec_mov_dict["DEBCRED"])))  # debito -> avere, credito -> dare

        elif type_movement == "Saldo Debito - Credito":
            if "ID_PAG" not in main_mov_dict.keys():
                raise WrongValueInsert("Tipo di pagamento non inserito")
            if "NOTE" not in spec_mov_dict.keys():
                spec_mov_dict["NOTE"] = ""
            dare_avere, importo = self.get_prev_deb_info(spec_mov_dict["ID_PREV_DEB_CRED"])
            # NB main_mov_dict["ID_PAG"] è già salvato del dizionario
            main_mov_dict["IMPORTO"] = importo
            main_mov_dict["DARE_AVERE"] = dare_avere
            main_mov_dict["NOTE"] = "[Saldo dei {} di id: {}] {}".format("crediti" if dare_avere == "1" else "debiti", spec_mov_dict["ID_PREV_DEB_CRED"], spec_mov_dict["NOTE"]).strip()

        elif type_movement == "Spesa di Mantenimento":
            if "DESCRIZIONE" not in spec_mov_dict.keys() or spec_mov_dict.get("DESCRIZIONE").strip() == "":
                raise WrongValueInsert("Descrizione non inserita")
            main_mov_dict["DARE_AVERE"] = 0  # è una spesa, valorizzo dare

        elif type_movement == "Spesa di Viaggio":
            if "VIAGGIO" not in spec_mov_dict.keys() or spec_mov_dict.get("VIAGGIO").strip() == "":
                raise WrongValueInsert("Viaggio non inserito")
            if "DESCRIZIONE" not in spec_mov_dict.keys() or spec_mov_dict.get("DESCRIZIONE").strip() == "":
                raise WrongValueInsert("Descrizione non inserita")
            main_mov_dict["DARE_AVERE"] = 0  # è una spesa, valorizzo dare

        # spec_mov_dict è corretto e compilato con eventuali valori di default
        logging.info("[%-10s]: verifica movimento - informazioni specifiche corrette: %s", "Wallet", Tools.list_to_str(spec_mov_dict))
        if not date_mov:  # il dizionario è vuoto, restituisce la data odierna
            data_movimento = datetime.now().strftime("%d-%m-%Y")
        else:
            data_movimento = self.check_date(date_mov)  # check sulla data del movimento
            if data_movimento is None:
                raise WrongValueInsert("Data movimento non valida")
        # data_movimento è corretta e comipilato con eventuali valori di default
        logging.info("[%-10s]: verifica movimento - data corretta: %s", "Wallet", date_mov)
        # valorizzo i campi per l'inserimento nel db e flaggo a True la variabile per inserire il movimento
        self.main_mov_dict = main_mov_dict
        self.spec_mov_dict = spec_mov_dict
        self.data_movimento = data_movimento
        self._ready_to_insert_data = True
        logging.info("[%-10s]: verifica movimento - pronto per inserire il movimento nel database" % "Wallet")

    def insert_movement(self):
        """Una volta valorizzati campi del movimento inserito con il metodo check_values() vengono create le istruzioni
        SQL (con il metodo self.format_sql_string()) per l'inserimento dei dati nel db"""

        if not self._ready_to_insert_data:
            logging.error("[%-10s]: inserimento movimento - errore - tentativo di inserimento di un movimento senza che i dati siano stati verificati" % "Wallet")
            raise WrongValueInsert("Dati da inserire non verificati")

        main_movement_query = ""                                            # query SQL per inserire il movimento generico
        spec_movement_query = ""                                            # query SQL per inserire il movimento specifico
        varchar_values = []                                                 # lista di elementi di tipo varchar, essi dovranno essere racchiusi da apici singoli nelle istruzioni SQL
        main_mov_id = ""                                                    # id del movimento principale appena inserito

        if self.type_movement == "Spesa Generica":
            varchar_values.append(self.spec_mov_dict.get("DESCRIZIONE"))
            spec_movement_query = self.format_sql_string("I", "SPESE_VARIE", insert_dict=
            {"ID_MOV": "{id}",
             "ID_TIPO_SPESA": self.spec_mov_dict.get("ID_TIPO_SPESA"),
             "DESCRIZIONE": self.spec_mov_dict.get("DESCRIZIONE")}, varchar_values=varchar_values)
        elif self.type_movement == "Spesa Fissa":
            varchar_values.append(self.spec_mov_dict.get("DESCRIZIONE"))
            spec_movement_query = self.format_sql_string("I", "SPESE_FISSE", insert_dict=
            {"ID_MOV": "{id}",
             "DESCRIZIONE": self.spec_mov_dict.get("DESCRIZIONE"),
             "MESE": self.data_movimento.split("-")[1]}, varchar_values=varchar_values)
        elif self.type_movement == "Stipendio":
            varchar_values.append(self.spec_mov_dict.get("PROVENIENZA"))
            varchar_values.append(self.spec_mov_dict.get("NOTE"))
            spec_movement_query = self.format_sql_string("I", "STIPENDI", insert_dict=
            {"ID_MOV": "{id}",
             "PROVENIENZA": self.spec_mov_dict.get("PROVENIENZA"),
             "MESE": int(self.data_movimento.split("-")[1]) - 1 if int(self.data_movimento.split("-")[1]) != 1 else 12,  # divido per il separatore, prendo il mese diminuito di uno
             "TOTALE": self.spec_mov_dict.get("TOTALE"),
             "NETTO": self.spec_mov_dict.get("NETTO"),
             "TRATTENUTE": self.spec_mov_dict.get("TRATTENUTE"),
             "RIMBORSO_SPESE": self.spec_mov_dict.get("RIMBORSO_SPESE"),
             "NOTE": self.spec_mov_dict.get("NOTE")}, varchar_values=varchar_values)
        elif self.type_movement == "Entrata":
            varchar_values.append(self.spec_mov_dict.get("ORIGINE"))
            varchar_values.append(self.spec_mov_dict.get("DESCRIZIONE"))
            spec_movement_query = self.format_sql_string("I", "ENTRATE", insert_dict=
            {"ID_MOV": "{id}",
             "ID_TIPO_ENTRATA": self.spec_mov_dict.get("ID_TIPO_ENTRATA"),
             "DESCRIZIONE": self.spec_mov_dict.get("DESCRIZIONE")}, varchar_values=varchar_values)
        elif self.type_movement == "Debito - Credito":
            varchar_values.append(self.spec_mov_dict.get("ORIGINE"))
            varchar_values.append(self.spec_mov_dict.get("DESCRIZIONE"))
            spec_movement_query = self.format_sql_string("I", "DEBITI_CREDITI", insert_dict=
            {"ID_MOV": "{id}",
             "DEBCRED": self.spec_mov_dict.get("DEBCRED"),
             "DESCRIZIONE": self.spec_mov_dict.get("DESCRIZIONE"),
             "ORIGINE": self.spec_mov_dict.get("ORIGINE"),
             "SALDATO": 0,
             "ID_MOV_SALDO": "NULL",
             "DATA_SALDO": "NULL"}, varchar_values=varchar_values)
        elif self.type_movement == "Saldo Debito - Credito":
            spec_movement_query = ""
            id_records = self.spec_mov_dict["ID_PREV_DEB_CRED"]
            for id_record in id_records:        # per ogni debito/credito nella lista aggiorno il relativo record nella tabella creando una sequenza di UPDATE
                spec_movement_query += self.format_sql_string("U", "DEBITI_CREDITI",
                                                               update_dict={"SALDATO": 1, "ID_MOV_SALDO": "{id}", "DATA_SALDO": "CONVERT(DATE, '{}', 105)".format(self.data_movimento)},
                                                               where_dict={"ID_MOV": id_record}) + "\n"
        elif self.type_movement == "Spesa di Mantenimento":
            varchar_values.append(self.spec_mov_dict.get("DESCRIZIONE"))
            spec_movement_query = self.format_sql_string("I", "SPESE_MANTENIMENTO", insert_dict=
            {"ID_MOV": "{id}",
             "DESCRIZIONE": self.spec_mov_dict.get("DESCRIZIONE")}, varchar_values=varchar_values)
        elif self.type_movement == "Spesa di Viaggio":
            varchar_values.append(self.spec_mov_dict.get("VIAGGIO"))
            varchar_values.append(self.spec_mov_dict.get("DESCRIZIONE"))
            spec_movement_query = self.format_sql_string("I", "SPESE_VIAGGI", insert_dict=
            {"ID_MOV": "{id}",
             "VIAGGIO": self.spec_mov_dict.get("VIAGGIO"),
             "DESCRIZIONE": self.spec_mov_dict.get("DESCRIZIONE")}, varchar_values=varchar_values)

        varchar_values.append(self.main_mov_dict.get("NOTE"))
        main_movement_query = self.format_sql_string("I", "MOVIMENTI", insert_dict=
        {"DATA_MOV": "CONVERT(DATE, '{}', 105)".format(self.data_movimento),
         "DATA_INS": "GETDATE()",
         "IMPORTO": self.main_mov_dict["IMPORTO"],
         "DARE_AVERE": self.main_mov_dict["DARE_AVERE"],
         "TIPO_MOV": self.main_mov_dict["TIPO_MOV"],
         "ID_PAG": self.main_mov_dict["ID_PAG"],
         "NOTE": self.main_mov_dict["NOTE"]}, varchar_values=varchar_values)

        try:
            # inserisco il movimento principale
            self.cursor.execute(main_movement_query)  # eseguo la INSERT per il movimento principale
            logging.debug("[%-10s]: inserimento movimento - esecuzione della stringa SQL: %s", "Wallet", main_movement_query)
            main_mov_id = self.get_last_prog(table_name="MOVIMENTI")  # trovo l'id del mov appena inserito

            # inserisco il movimento specifico
            self.cursor.execute(spec_movement_query.format(id=main_mov_id))  # eseguo la/le INSERT/UPDATE per il movimento specifico
            logging.debug("[%-10s]: inserimento movimento - esecuzione della stringa SQL: %s", "Wallet", spec_movement_query.format(id=main_mov_id))

        except pyodbc.Error as err:     # errore, propago l'eccezione verso il livello più esterno ma salvo l'errore per inserirlo nel log
            logging.error("[%-10s]: inserimento movimento - errore - trace: %s", "Wallet", str(err))
            self.cursor.rollback()
            raise FatalError("Errore nell'inserimento del movimento {}, consulta il log per maggiori dettagli".format("principale" if main_mov_id == "" else "specifico"))

        else:
            logging.info("[%-10s]: inserimento movimento - inserimento riuscito", "Wallet")
            self.type_movement = ""                     # rimuovo le informazioni salvate
            self.data_movimento = ""
            self.main_mov_dict = {}
            self.spec_mov_dict = {}
            time.sleep(0.1)    # metto in pausa per 0.1 secondi per evitare che la (bassa) precisione di DATETIME di SQL scriva valori uguali

        finally:
            self._ready_to_insert_data = False                # ho inserito il movimento oppure ho avuto un errore imprevisto, la resetto a False

    def close_wallet(self):
        """concludo il log"""
        self.cursor.close()
        self.connection.close()
        logging.info("[%-10s]: chiusura di wallet e del collegamento al database... " % "Wallet")
        logging.info("[%-10s]: %s", "Wallet", "*" * 80)

    def backup_database(self, db_name, backup_path):
        """Esegue un backup del db wallet presente su SQL Server"""
        if not os.path.isabs(backup_path):
            backup_path = os.path.normpath(os.path.join(os.getcwd(), backup_path))
        backup_name = "{}_{}.bak".format(db_name, datetime.now().strftime("%d-%m-%Y"))
        sql_string = self.format_sql_string(suide="E",
                                            proc_name="BK_DATABASE",
                                            proc_args_dict={"bk_name": backup_name, "bk_path": backup_path, "db_to_backup": db_name},
                                            varchar_values=[backup_name, backup_path, db_name])
        try:
            logging.debug("[%-10s]: creazione backup database: %s - esecuzione della stringa SQL: %s", "Wallet", db_name, sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]: creazione backup database: %s - errore - trace: %s", "Wallet", db_name, str(error))
            raise FatalError("Errore nel backup del database, consulta il log per maggiori dettagli")
        else:
            logging.info("[%-10s]: creazione backup database: %s - backup %s creato in %s", "Wallet", db_name, backup_name, backup_path)

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

    def get_prev_deb_info(self, id_records):        # potrebbe eseguire una sp
        """Da una lista di id di debiti e/o crediti (NB di cui è già stato verificata la provenienza dalla stessa entità)
         restituisce l'importo come somma di valori positivi (crediti) e negativi (debiti) dei movimenti selezionati e
         il dare_avere valorizzato di conseguenza"""
        sql_string_total = self.format_sql_string(suide="S",
                                                   table_name="MOVIMENTI mv",
                                                   field_select_list=["cast(sum(case when DARE_AVERE = 1 then importo * -1 else importo end) as decimal(9, 2)) as importo"],
                                                   join_type="I",
                                                   join_table="DEBITI_CREDITI dc",
                                                   join_dict={"mv.id": "dc.ID_MOV"}) + "\nWHERE dc.id_mov IN ({})".format(
            Tools.list_to_str(id_records))
        try:
            logging.debug("[%-10s]: raccolta info dai deb_cred di id in %s - esecuzione della stringa SQL: %s", "Wallet", str(id_records), sql_string_total)
            self.cursor.execute(sql_string_total)
        except pyodbc.Error as error:
            logging.error("[%-10s]: raccolta info dai deb_cred di id in %s - errore - trace: %s", "Wallet",
                          Tools.list_to_str(id_records), str(error))
            raise FatalError("Errore nel database, consulta il log per maggiori dettagli")
        else:
            importo = self.cursor.fetchval()
            if importo is not None:
                importo = float(importo)
                if importo <= 0:         # se importo è negativo o 0 => è una spesa, rimetto l'importo come positivo
                    importo *= -1
                    dare_avere = 0
                else:                   # se importo è positivo => è un'entrata
                    dare_avere = 1
                logging.debug("[%-10s]: raccolta info dai deb_cred di id in %s: - esecuzione riuscita", "Wallet", str(id_records))
                return dare_avere, importo
            else:
                logging.error("[%-10s]: raccolta info dai deb_cred di id in %s: &s - errore: importo nullo", "Wallet", str(id_records))
                raise FatalError("Errore nel risalire ai debiti/crediti selezionati")

    def get_movements(self, type_mov=None, name_mov=None):
        partial_sql = partial(self.format_sql_string,
                              suide="S",
                              table_name="MAP_MOVIMENTI",
                              field_select_list=["ID", "DESCRIZIONE"],
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
            type_movements_dict = {}
            for row in self.cursor:
                type_movements_dict[row.ID] = row.DESCRIZIONE
            logging.debug("[%-10s]: raccolta tipi di movimenti - esecuzione riuscita, valori trovati - %s", "Wallet",
                          Tools.list_to_str(type_movements_dict))
            return type_movements_dict

    def get_info_db(self, info_type):
        """Restituisce un dizionario sui tipi di pagamento nel formato {id_pagamento: nome_pagamento}"""
        _types = {"pagamenti": "MAP_PAGAMENTI", "spese_varie": "MAP_SPESE_VARIE", "entrate": "MAP_ENTRATE"}
        try:
            sql_string = self.format_sql_string(suide="S",
                                                 table_name=_types[info_type],
                                                 field_select_list=["ID", "DESCRIZIONE"],
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
            info_data = {}
            for row in self.cursor:
                info_data[row[0]] = row[1]
            logging.debug("[%-10s]: raccolta tipi di %s - esecuzione riuscita", "Wallet", info_type)
            return info_data

    # def get_type_payments(self):
    #     """Restituisce un dizionario sui tipi di pagamento nel formato {id_pagamento: nome_pagamento}"""
    #     sql_string = self.format_sql_string(suide="S",
    #                                          table_name="MAP_PAGAMENTI",
    #                                          field_select_list=["ID", "DESCRIZIONE"],
    #                                          order_by_dict={"DESCRIZIONE": "ASC"})
    #     try:
    #         logging.debug("[%-10s]: raccolta tipi di pagamenti - esecuzione della stringa SQL: %s", "Wallet", sql_string)
    #         self.cursor.execute(sql_string)
    #     except pyodbc.Error as error:
    #         logging.error("[%-10s]:  raccolta tipi di pagamenti - errore - trace: {}", "Wallet", str(error))
    #         raise FatalError("Errore nella raccolta dei tipi di pagamenti, consulta il log per maggiori dettagli")
    #     else:
    #         type_payments_dict = {}
    #         for row in self.cursor:
    #             type_payments_dict[row[0]] = row[1]
    #         logging.debug("[%-10s]: raccolta tipi di pagamenti - esecuzione riuscita" % "Wallet")
    #         return type_payments_dict
    #
    # def get_type_spec_movements(self):
    #     """Restituisce un dizionario sui tipi di spesa generica nel formato {id_spesa: nome_spesa}"""
    #     sql_string = self.format_sql_string(suide="S",
    #                                          table_name="MAP_SPESE_VARIE",
    #                                          field_select_list=["ID", "DESCRIZIONE"],
    #                                          order_by_dict={"DESCRIZIONE": "ASC"})
    #     try:
    #         logging.debug("[%-10s]: raccolta tipi di spese variabili - esecuzione della stringa SQL: %s", "Wallet", sql_string)
    #         self.cursor.execute(sql_string)
    #     except pyodbc.Error as error:
    #         logging.error("[%-10s]: raccolta tipi di spese variabili - errore - trace: %s", "Wallet", str(error))
    #         raise FatalError("Errore nella raccolta dei tipi di spese variabili, consulta il log per maggiori dettagli")
    #     else:
    #         type_spec_movments_dict = {}
    #         for row in self.cursor:
    #             type_spec_movments_dict[row[0]] = row[1]
    #         logging.debug("[%-10s]: raccolta tipi di spese variabili - esecuzione riuscita, valori trovati - %s", "Wallet",
    #                       Tools.list_to_str(type_spec_movments_dict))
    #         return type_spec_movments_dict
    #
    # def get_type_entrate(self):
    #     """Restituisce un dizionario sui tipi di entrata nel formato {id_entrata: nome_entrata}"""
    #     sql_string = self.format_sql_string(suide="S",
    #                                          table_name="MAP_ENTRATE",
    #                                          field_select_list=["ID", "DESCRIZIONE"],
    #                                          order_by_dict={"DESCRIZIONE": "ASC"})
    #     try:
    #         logging.debug("[%-10s]: raccolta tipi di entrate - esecuzione della stringa SQL: %s", "Wallet", sql_string)
    #         self.cursor.execute(sql_string)
    #     except pyodbc.Error as error:
    #         logging.error("[%-10s]: raccolta tipi di entrate - errore - trace: %s", "Wallet", str(error))
    #         raise FatalError("Errore nella raccolta dei tipi di entrate, consulta il log per maggiori dettagli")
    #     else:
    #         type_entrate_dict = {}
    #         for row in self.cursor:
    #             type_entrate_dict[row[0]] = row[1]
    #         logging.debug("[%-10s]: raccolta tipi di entrate - esecuzione riuscita, valori trovati - %s", "Wallet",
    #                       Tools.list_to_str(type_entrate_dict))
    #         return type_entrate_dict

    def get_last_prog(self, table_name):
        """Recupera l'ultimo id inserito nella tabella passata"""
        sql_string = self.format_sql_string(suide="S",
                                             table_name=table_name,
                                             field_select_list=["TOP 1 ID"],
                                             order_by_dict={"ID": "DESC"})
        try:
            logging.debug("[%-10s]: recupero ultimo id da tabella %s - esecuzione della stringa SQL: %s", "Wallet", table_name, sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:
            logging.error("[%-10s]: recupero ultimo id da tabella %s - errore - trace: %s", "Wallet", table_name, str(error))
            raise FatalError("Errore nel recupero ultimo id da tabella {}, consulta log per maggiori dettagli".format(table_name))
        else:
            last_id = self.cursor.fetchval()  # recupero l'ultimo id inserito
            logging.debug("[%-10s]: recupero ultimo id da tabella %s - esecuzione riuscita", "Wallet", table_name)
            # se last_id is None la tab è vuota, creo id con progressivo 1
            return "1" if last_id is None else last_id

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

    def check_ids_to_pay(self, ids_deb_cred_list):
        """Verifica che gli id, eventualmente più di uno, debiti o crediti, appartengano alla stessa persona"""
        sql_string = self.format_sql_string(suide="S",
                                             field_select_list=["count(distinct ORIGINE)"],
                                             table_name="DEBITI_CREDITI dc",
                                             join_type="I",
                                             join_table="MOVIMENTI mv",
                                             join_dict={"mv.id": "dc.id_mov"})
        sql_string += " where mv.id in ({})".format(Tools.list_to_str(ids_deb_cred_list))

        try:
            logging.debug("[%-10s]: controllo omogeneità origine - esecuzione della stringa SQL: %s", "Wallet", sql_string)
            self.cursor.execute(sql_string)
        except pyodbc.Error as error:  # errore generico, lo propago
            logging.error("[%-10s]: controllo omogeneità origine - errore - trace: %s", "Wallet", str(error))
            raise FatalError("Errore del controllo dei dati inseriti, consulta il log per maggiori dettagli")
        else:   # se c'è omogeneità il count distinct deve dare come risultato 1 (ovvero un unico destinatario)
            count_values_in_select = int(self.cursor.fetchval())
            logging.debug("[%-10s]: controllo omogeneità origine - %s", "Wallet", "record omogenei" if count_values_in_select == len(ids_deb_cred_list) else "record non omogenei")
            return count_values_in_select == 1

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
                          proc_name=None,
                          proc_args_dict=None):
        """Crea e formatta un'instruzione SQL di tipo suid (SELECT, UPDATE, INSERT, DELETE)
            - suid -> ha come valore 'S' SELECT, 'U' UPDATE, 'I' INSERT, 'D' DELETE, 'E' EXEC (esegue procedura)
            - table_name -> nome della tabella in questione,
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
            - proc_name -> nome procedura da eseguire
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
                if join_type in join_types_dict.keys() and join_table and isinstance(join_dict,
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
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in
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
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in
                                             update_dict.items())
                sql_string = " ".join([sql_string, fields_to_update])

            else:
                raise WrongValueInsert(
                    "Non è stata fornita la lista dei campi da modificare oppure il tipo non è corretto, deve essere dict")

            if isinstance(where_dict,
                          dict):  # se where_dict è tipo dict aggiungo anche le restrizioni tramite WHERE statement
                fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in
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
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else str(value) for value in
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
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in
                                                where_dict.items())
                sql_string = " ".join([sql_string, "WHERE", fields_to_filter])

            elif where_dict is not None:
                raise WrongValueInsert(
                    "è stato passato un parametro non valido per la condizione WHERE, deve essere dict")

            else:
                raise WrongValueInsert("Non è possibile eliminare per intero una tabella!")
        elif suide == "E":
            sql_string = "exec {}".format(proc_name)
            if isinstance(proc_args_dict, dict):  # se proc_args_dict <> da None aggiungo anche la lista di argomenti
                args = ", ".join("@{} = {}".format(key, "'{}'".format(
                    Tools.escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in
                                 proc_args_dict.items())
                sql_string = " ".join([sql_string, args])
        return sql_string

    def check_date(self, date: datetime):
        """Verifica che il dizionario in input contenga una data e la restituisce come istanza di datetime"""
        count = 0  # se arriva a 3 alla fine del ciclo restituisce data odierna, vedi poi
        time_dict = {"day": range(1, 32), "month": range(1, 13), "year": range(2000, 2026)}
        for time_period, time_range in time_dict.items():
            if time_period not in date.keys() or date[time_period].strip() == "":  # se manca l'elemento oppure è vuoto aumento count
                count += 1
            else:  # in caso contrario allora esiste e non è vuoto
                try:
                    if int(date[
                               time_period]) not in time_range:  # se è all'esterno del relativo range il numero non è valido e quindi la data
                        return None
                except (ValueError, TypeError):  # l'elemento non è in formato numerico intero, data non valida
                    return None
        if count == 3:  # se per tre volte l'elemento mancava oppure era vuoto allora restituisce data odierna
            return datetime.now().strftime("%d-%m-%Y")
        elif count == 0:  # crea la data con i tre parametri passati
            return datetime(int(date["year"]), int(date["month"]), int(date["day"])).strftime("%d-%m-%Y")
        else:  # mancano uno o due elementi, data non valida
            return None


if __name__ == "__main__":
    pass



