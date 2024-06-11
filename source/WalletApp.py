import logging
import os
from datetime import date
import Wallet
import Tools
from kivy.config import Config

Config.read(os.path.join(os.getcwd(), "..\\settings\\config_wallet.ini"))
Tools.set_center_app(Config)

from kivy.lang import Builder
from Screens import *

log_levels = {10: logging.DEBUG, 20: logging.INFO, 30: logging.WARNING, 40: logging.ERROR, 50: logging.CRITICAL}


class AppException(Exception):
    """Se si verifica un errore interno a livello di funzionamento di widget"""
    def __init__(self, error_text):
        super().__init__()
        self.error_text = error_text  # creo la proprietà di classe per avere maggiori informazioni sull'errore verificatosi

    def __str__(self):
        return self.error_text


class WalletApp(App):
    """Applicazione principale che gestisce il front end con l'utente, essa permette:
        1) la modifica delle informazioni, inserendo nuovi movimenti o saldando debiti/crediti esistenti
        2) l'accesso alla BI per analisi"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = Config["wallet_app"]["app_name"]               # nome dell'app
        self.dsn = Config["database"]["dsn_name"].strip("'")                        # istanza di wallet per accedere al database
        self.bi_file_path = Config["bi"]["qlik_file_path"]               # istanza dell'app di QlikView
        self.kv_files = Config["kivy_files"].values()               # file di stile .kv
        self.db_name = Config["database"]["database_name"]
        self.backup_path = Config["database"]["backup_path"]
        self._stopped = False                                       # proprietà di servizio, vedi self.on_stop()
        self.date_dict = {}                                         # data movimento
        self.main_mov_dict = {}                                     # informazioni generali (comuni ad ogni tipo di spesa/entrata)
        self.spec_mov_dict = {}                                     # informazioni specifiche della spesa/entrata
        self.manager = None                                        # istanza di ScreenManager per muoversi tra le schermate
        self.wallet_instance = None
        self.qlik_app = None
        self.create_logger(logger_name="wallet_logger",
                            log_level=log_levels[Config.getint("log", "level")],
                            log_path=Config["log"]["path_log_file"],
                            log_name=Config["log"]["name_log_file"],
                            fmt=Config["log"]["format_log_file"])
        logging.info("[%-10s]: %s", "WalletApp", "#" * 80)
        logging.info("[%-10s]: avvio app - applicazione avviata" % "WalletApp")

    def create_logger(self, logger_name, log_level, log_name, log_path, fmt):
        """Crea un file di log con livello, percorso, nome e formattazione dei record passati come parametri, richiamando
        poi il modulo logging sarà possibile scrivere su di esso"""
        logger = logging.getLogger(logger_name)
        logging.root = logger
        logger.setLevel(log_level)
        file_handler = logging.FileHandler(filename=os.path.join(log_path, log_name.format(date.today().strftime("%d-%m-%Y"))))
        log_formatter = logging.Formatter(fmt=fmt)
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    def build(self):
        try:
            for kv_file in self.kv_files:
                Builder.load_file(kv_file)
        except Exception as error:
            raise AppException("Errore GUI - " + str(error))
        else:
            self.manager = ManagerScreen()
            logging.info("[%-10s]: avvio app - caricati i file di stile .kv, creato ScreenManager e Screen di login" % "WalletApp")
            return self.manager

    def login(self, user, pwd, auto_login=False):
        if auto_login is True:
            self.wallet_instance = Wallet.Wallet(self.dsn)
            self.manager.set_movements(self.wallet_instance.get_movements())
            return True
        if user.strip() == "" or pwd.strip() == "":
            raise AppException("Credenziali mancanti")
        self.wallet_instance = Wallet.Wallet(self.dsn)
        self.manager.set_movements(self.wallet_instance.get_movements())
        return self.wallet_instance.login_wallet(user.strip(), pwd.strip())

    def open_BI(self):
        if self.qlik_app is None:
            self.qlik_app = Wallet.QlikViewApp(self.bi_file_path)
        if self.wallet_instance is None:
            self.wallet_instance = Wallet.Wallet(self.dsn)
        # try:
        user, pwd = self.wallet_instance.get_bi_credentials()
        self.qlik_app.open(user, pwd)

        # NB move it
        # except Wallet.FatalError as generic_error:
        #     Factory.ErrorPopup(err_text=str(generic_error)).open()

    def insert_movement(self):
        try:
            self.wallet_instance.check_values(type_movement=self.manager.type_mov,
                                              date_mov=self.date_dict,
                                              main_mov_dict=self.main_mov_dict,
                                              spec_mov_dict=self.spec_mov_dict)
            self.wallet_instance.insert_movement()
        except (Wallet.WrongValueInsert, Wallet.FatalError) as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            Factory.SingleChoicePopup(info="MOVIMENTO INSERITO", func_to_exec=self.manager.go_to_main_screen).open()

    def drop_records(self, list_records, type_movement):
        """Ricevo in argomento una lista di id, ciascuno corrispondente ad un movimento, da eliminare
            - list_records -> lista di id di movimenti da rimuovere
            - type_movement -> tipo di movimento a cui gli id appartengono (a cui corrisponde la relativa tabella nel db"""
        try:
            self.wallet_instance.drop_records(list_records, type_movement)
        except (Wallet.WrongValueInsert, Wallet.FatalError, Tools.WrongSQLstatement) as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            Factory.SingleChoicePopup(info="Movimenti selezionati eliminati").open()

    def backup_database(self):
        """Crea un backup del database al percorso inserito nel file .ini, il formato del nome del backup viene
        stabilito più a basso livello (metodo Wallet.backup_database)"""
        try:
            self.wallet_instance.backup_database(self.db_name, self.backup_path)
        except Exception as err:
            Factory.ErrorPopup(err_text=str(err)).open()
        else:
            Factory.SingleChoicePopup(info="Backup creato con successo").open()

    def on_stop(self):
        """Non è chiaro perchè ma il metodo app.stop() viene chiamato due volte, per evitare di scrivere due volte sul log
        utilizzo il parametro _stopped"""
        if not self._stopped:
            self._stopped = True
            if self.wallet_instance:
                self.wallet_instance.close_wallet()
            if self.qlik_app:
                self.qlik_app.close()
            logging.info("[%-10s]: chiusura app - applicazione chiusa" % "WalletApp")
            logging.info("[%-10s]: %s", "WalletApp",  "#" * 80)

    def get_movements(self, type_mov=None, name_mov=None):
        return self.wallet_instance.get_movements(type_mov, name_mov)

    def get_type_payments(self):
        return self.wallet_instance.get_type_payments()

    def get_type_spec_movements(self):
        return self.wallet_instance.get_type_spec_movements()

    def get_type_entrate(self):
        return self.wallet_instance.get_type_entrate()


if __name__ == "__main__":
    app = WalletApp()
    app.run()
