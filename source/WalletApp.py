import logging
import os
from datetime import date
from win32api import GetSystemMetrics
import Wallet

from kivy.config import Config
Config.read(os.path.join(os.getcwd(), "..\\settings\\config_wallet.ini"))
from kivy.lang import Builder
from Screens import *
from Popups import *

log_levels = {10: logging.DEBUG, 20: logging.INFO, 30: logging.WARNING, 40: logging.ERROR, 50: logging.CRITICAL}


class AppException(Exception):
    """Se si verifica un errore interno a livello di funzionamento di widget"""
    def __init__(self, error_text):
        super().__init__()
        self.error_text = error_text  # creo la proprietà di classe per avere maggiori informazioni sull'errore verificatosi

    def __str__(self):
        return self.error_text


class WalletApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = None
        self.title = Config["wallet_app"]["app_name"]               # nome dell'app
        self.max_rows_to_show = Config.getint("wallet_app", "max_rows_to_show")            # max righe mostrate in SowMovementScreen
        self.default_rows_to_show = Config.getint("wallet_app", "default_rows_to_show")   # default righe mostrate in SowMovementScreen
        self.dsn = Config["database"]["dsn_name"].strip("'")        # istanza di wallet per accedere al database
        self.bi_file_path = Config["bi"]["qlik_file_path"]          # istanza dell'app di QlikView
        self.kv_files = Config["kivy_files"].values()               # file di stile .kv
        self.db_name = Config["database"]["database_name"]
        self.backup_path = Config["database"]["backup_path"]
        self.create_logger(logger_name="wallet_logger",
                           log_level=log_levels[Config.getint("log", "level")],
                           log_path=Config["log"]["path_log_file"],
                           log_name=Config["log"]["name_log_file"],
                           fmt=Config["log"]["format_log_file"])
        self.set_center_app()
        logging.info("[%-10s]: %s", "WalletApp", "#" * 80)
        logging.info("[%-10s]: avvio app - applicazione avviata" % "WalletApp")
        self._stopped = False                                       # proprietà di servizio, vedi self.on_stop()
        # self.date_dict = {}                                         # data movimento
        # self.main_mov_dict = {}                                     # informazioni generali (comuni ad ogni tipo di spesa/entrata)
        # self.spec_mov_dict = {}                                     # informazioni specifiche della spesa/entrata
        # self.manager = None                                         # istanza di ScreenManager per muoversi tra le schermate
        self.wallet_instance = Wallet.Wallet(self.dsn)
        self.qlik_app = Wallet.QlikViewApp(self.bi_file_path)

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
        for kv_file in self.kv_files:
            try:
                Builder.load_file(kv_file)
            except Exception as error:
                logging.error("[%-10s]: avvio app - errore file %s - trace: %s", "WalletApp", kv_file, str(error))
                raise AppException(str(error))
        self.manager = ManagerScreen()
        logging.info("[%-10s]: avvio app - caricati i file di stile .kv, creato ScreenManager e Screen di login" % "WalletApp")
        return self.manager

    def login(self, user, pwd):
        if user.strip() == "" or pwd.strip() == "":
            raise AppException("Credenziali mancanti")
        return self.wallet_instance.login_wallet(user.strip(), pwd.strip())

    def open_BI(self):
        user, pwd = self.wallet_instance.get_bi_credentials()
        self.qlik_app.open(user, pwd)

    def insert_movement(self, data_movement):
        try:
            self.wallet_instance.check_values(data_info=data_movement)
            self.wallet_instance.insert_movement()
        except Wallet.FatalError as err:        # Nb why?
            raise err

    def drop_records(self, list_records, type_movement):
        """Ricevo in argomento una lista di id, ciascuno corrispondente ad un movimento, da eliminare
            - list_records -> lista di id di movimenti da rimuovere
            - type_movement -> tipo di movimento a cui gli id appartengono (a cui corrisponde la relativa tabella nel db"""
        self.wallet_instance.drop_records(list_records, type_movement)

    def turn_deb_cred_into_mov(self, list_records):
        self.wallet_instance.turn_deb_cred_into_mov(list_records)

    def backup_database(self):
        """Crea un backup del database al percorso inserito nel file .ini, il formato del nome del backup viene
        stabilito più a basso livello (metodo Wallet.backup_database)"""
        self.wallet_instance.backup_database(self.db_name, self.backup_path)

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

    def set_center_app(self):
        """A seconda dello schermo che uso, centro l'app nel monitor"""
        width_app = Config.getint("graphics", "width")
        height_app = Config.getint("graphics", "height")
        width_screen = GetSystemMetrics(0)
        height_screen = GetSystemMetrics(1)
        Config.set("graphics", "top", str((height_screen - height_app) // 2))
        Config.set("graphics", "left", str((width_screen - width_app) // 2))
        Config.write()

    def get_max_rows_to_show(self):
        return self.max_rows_to_show

    def get_default_rows_to_show(self):
        return self.default_rows_to_show

    def get_movements(self, type_mov=None):
        return self.wallet_instance.get_movements(type_mov, None)

    def get_type_payments(self):
        return self.wallet_instance.get_info_db("pagamenti")

    def get_type_spec_movements(self):
        return self.wallet_instance.get_info_db("spese_varie")

    def get_type_entrate(self):
        return self.wallet_instance.get_info_db("entrate")


if __name__ == "__main__":
    app = WalletApp()
    app.run()
