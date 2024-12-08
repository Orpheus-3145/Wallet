import logging
import os
from datetime import date
import tkinter as tk
# import win32com.client as win32         # per aprire applicazioni win
# import pywintypes                       # per gestire alcune eccezioni legate al modulo di cui sopra

import Tools
import Wallet
from AppExceptions import *

from kivy.config import Config
DEF_LOG_LVL = 20

# if os.environ.get("WalletAppPath") == os.getcwd():
#     os.chdir("_internal")
# else:
#     os.chdir("..")

LOG_PATH = Tools.get_abs_path("logs")
CONFIG_PATH = Tools.get_abs_path("settings/config_wallet.ini")

Config.read(CONFIG_PATH)

from kivy.lang import Builder
from kivy.core.window import Window
from Screens import *
from Popups import *

class WalletApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stopped = False
        self.wallet_instance = None
        self.config_info = {}
        self.stored_procs = {}
        self.create_logger(LOG_PATH, Config.get("log", "log_level", fallback=DEF_LOG_LVL))
        self.read_config(Config)

    def read_config(self, config):
        try:
            self.config_info["kv_files"] = [Tools.get_abs_path(kv_file) for kv_file in config["kivy_files"].values()]
            self.config_info["host"] = config["database"]["host"]
            self.config_info["port"] = config["database"]["port"]
            self.config_info["user"] = config["database"]["user"]
            self.config_info["password"] = config["database"]["password"]
            self.config_info["backup_path"] = Tools.get_abs_path(config["database"]["backup_path"])
            self.config_info["background_img_path"] = Tools.get_abs_path(config["graphics"]["background_img_path"])
            self.config_info["logo_path"] = Tools.get_abs_path(config["graphics"]["logo_path"])
            self.config_info["font_name"] = config["kivy"]["font_name"]
            self.config_info["font_size"] = config.getint("kivy", "font_size")
            self.config_info["width_app"] = config.getint("graphics", "width")
            self.config_info["height_app"] = config.getint("graphics", "height")
            self.config_info["max_rows_to_show"] = config.getint("widgets", "max_rows_to_show")  # max righe mostrate in SowMovementScreen
            self.config_info["default_rows_to_show"] = config.getint("widgets", "default_rows_to_show")  # default righe mostrate in SowMovementScreen
            self.config_info["colors"] = {}
            for color_rgba in config["colors"].keys():
                self.config_info["colors"][color_rgba] = Tools.str_to_list_float(config["colors"][color_rgba])
        except (KeyError, ValueError) as error:
            self.update_log("errore nel file .ini - trace: %s", 40, str(error))
            raise AppException("Errore nel file .ini - trace: {}".format(str(error)))

    def create_logger(self, log_path, log_level):
        log_name = "Logfile_{}.log".format(date.today().strftime("%d-%m-%Y"))
        log_path = os.path.join(log_path, log_name)
        log_levels = {10: logging.DEBUG, 20: logging.INFO, 30: logging.WARNING, 40: logging.ERROR, 50: logging.CRITICAL}
        log_level_is_wrong = False
        try:
            log_level = int(log_level)
            if log_level not in log_levels:
                raise KeyError()
        except KeyError:
            log_level_is_wrong = True
            log_level = 20
        finally:
            log_level = log_levels[log_level]
        log_encoding = "utf-8"
        log_format = "%(asctime)s | %(levelname)-9s | %(message)s"
        log_date_format = "%m/%d/%Y %H:%M:%S"

        logger = logging.getLogger(__name__)
        logging.root = logger
        logger.setLevel(log_level)
        file_handler = logging.FileHandler(filename=log_path, encoding=log_encoding)
        log_formatter = logging.Formatter(fmt=log_format, datefmt=log_date_format)
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

        self.update_log("#" * 80, 20)
        self.update_log("app avviata", 20)
        if log_level_is_wrong is True:
            self.update_log("livello log in .ini file non valido [usage: 10, 20, 30, 40, 50]", 30)

    def update_log(self, message, level, *args):
        log_alerts = {10: logging.debug, 20: logging.info, 30: logging.warning, 40: logging.error, 50: logging.critical}
        try:
            log_alerts[level](message, *args)
        except KeyError:
            self.update_log("invalid log level provided: {}, original message: '{}'".format(level, message), 30, *args)

    def build(self):
        root = tk.Tk()
        root.withdraw()
        width_screen = root.winfo_screenwidth()
        height_screen = root.winfo_screenheight()
        
        Window.left = (width_screen - self.config_info["width_app"]) // 2
        Window.top = (height_screen - self.config_info["height_app"]) // 2
        for kv_file in self.config_info["kv_files"]:
            try:
                Builder.load_file(kv_file)
            except Exception as error:
                self.update_log("caricamento front-end - errore in %s - %s", 40, kv_file, str(error))
                raise AppException("Caricamento front-end, errore: ".format(str(error)))
            self.update_log("caricamento front-end - %s", 10, kv_file)
        return ManagerScreen()

    def connect(self):
        try:
            self.wallet_instance = Wallet.Wallet(self.config_info["host"], self.config_info["port"], self.config_info["user"], self.config_info["password"])
        except SqlError as db_err:
            self.update_log("errore connessione - %s", 40, str(db_err))
            raise AppException("Connessione al database fallita, consulta il log per ulteriori dettagli")
        else:
            self.update_log("connessione al database effettuata", 10)

    def login(self, user, pwd, autologin):
        if autologin is True:
            self.connect()
            return True
        elif user == "" or pwd == "":
            raise AppException("Credenziali mancanti")
        self.connect()
        login_success = self.wallet_instance.login_wallet(user.strip(), pwd.strip())
        if login_success is True:
            self.update_log("utente %s ha effettuato l'accesso", 20, user)
        return login_success

    def insert_movement(self, id_mov, data_movement):
        try:
            self.update_log("inserimento nuovo movimento tipo %s", 10, id_mov)
            self.wallet_instance.insert_movement(id_mov=id_mov, data_info=data_movement)
        except (InternalError, WrongValueInsert, SqlError) as error:
            if isinstance(error, InternalError) is True:
                self.update_log("errore inserimento - %s", 40, str(error))
                raise AppException("Movimento non inserito, consulta il log per ulteriori dettagli")
            else:       # an info is missing or wrong
                raise AppException(str(error))
        else:
            self.update_log("inserimento nuovo movimento tipo %s riuscito", 20, id_mov)

    def drop_records(self, list_records):
        count_errs = 0
        for record_to_drop in list_records:
            try:
                self.wallet_instance.drop_record(record_to_drop)
            except SqlError as error:
                self.update_log("rimozione movimento id: %s fallita - trace: %s", 40, record_to_drop, str(error))
                count_errs = count_errs + 1
            else:
                self.update_log("movimento id: %s rimosso", 20, record_to_drop)
        if count_errs > 0:
            raise AppException("Errore nella rimozione record(s), consulta il log per ulteriori dettagli")

    def turn_deb_cred_into_mov(self, list_records):
        failed = False
        for record_to_turn in list_records:
            try:
                self.wallet_instance.turn_deb_cred_into_mov(record_to_turn)
            except SqlError as error:
                self.update_log("trasformazione deb/cred id %s fallita - %s", 40,  record_to_turn, str(error))
                failed = True
            else:
                self.update_log("deb/cred id %s trasformato", 20, record_to_turn)
        if failed is True:
            raise AppException("Errore nella trasformazione record(s), consulta il log per ulteriori dettagli")

    def backup_database(self):
        backup_path = self.config_info["backup_path"]
        backup_name = "Wallet_{}.bak".format(datetime.now().strftime("%d-%m-%Y"))
        if not os.path.isabs(backup_path):
            backup_path = os.path.normpath(os.path.join(os.getcwd(), backup_path))
        for i in range(1, 100):
            if not os.path.exists(os.path.join(backup_path, backup_name)):
                break
            backup_name = "Wallet_{}_{}.bak".format(datetime.now().strftime("%d-%m-%Y"), i)
        else:
            self.update_log("max 100 backup al giorno", 40, os.path.dirname(backup_path))
            raise AppException("Raggiunto limite numero backup in {}".format(os.path.dirname(backup_path)))
        backup_path = os.path.join(backup_path, backup_name)
        try:
            self.wallet_instance.backup_database(backup_path)
        except SqlError as error:
            self.update_log("creazione backup %s in %s fallita - %s", 40, os.path.basename(backup_path), os.path.dirname(backup_path), str(error))
            raise AppException("Backup fallito, consulta il log per ulteriori dettagli")
        else:
            self.update_log("creato backup in %s", 20, os.path.dirname(backup_path))

    def on_stop(self):
        """Non è chiaro perchè ma il metodo app.stop() viene chiamato due volte, per evitare di scrivere due volte sul log
        utilizzo il parametro _stopped"""
        if not self._stopped:
            self._stopped = True
            if self.wallet_instance:
                self.wallet_instance.close_wallet()
        self.update_log("app chiusa", 20)
        self.update_log("#" * 80, 20)

    # db interrogations
    def get_movements(self, movs_to_drop=None):
        if movs_to_drop is None:
            movs_to_drop = []
        movements = self.wallet_instance.get_info_db("movimenti")
        for mov_to_drop in movs_to_drop:
            for key_mov, name_mov in movements.items():
                if name_mov == mov_to_drop:
                    del movements[key_mov]
                    break
        return movements

    def get_type_accounts(self):
        try:
            return self.wallet_instance.get_info_db("conti")
        except SqlError as db_err:
            self.update_log("errore nella lettura del database - trace: %s", 40, str(db_err))
            raise AppException("Errore database, consulta il log per ulteriori dettagli")

    def get_type_spec_movements(self):
        try:
            return self.wallet_instance.get_info_db("spese_varie")
        except SqlError as db_err:
            self.update_log("errore nella lettura del database - trace: %s", 40, str(db_err))
            raise AppException("Errore database, consulta il log per ulteriori dettagli")

    def get_type_entrate(self):
        try:
            return self.wallet_instance.get_info_db("entrate")
        except SqlError as db_err:
            self.update_log("errore nella lettura del database - trace: %s", 40, str(db_err))
            raise AppException("Errore database, consulta il log per ulteriori dettagli")

    def get_open_deb_creds(self):
        try:
            return self.wallet_instance.get_open_deb_creds()
        except SqlError as db_err:
            self.update_log("errore nella lettura del database - trace: %s", 40, str(db_err))
            raise AppException("Errore database, consulta il log per ulteriori dettagli")

    def get_last_n_records(self, id_mov, n_records):
        try:
            return self.wallet_instance.get_last_n_records(id_mov, n_records)
        except SqlError as db_err:
            self.update_log("errore nella lettura del database - trace: %s", 40, str(db_err))
            raise AppException("Errore database, consulta il log per ulteriori dettagli")

    # getters from settings file
    def get_max_rows_to_show(self):
        return self.config_info["max_rows_to_show"]

    def get_default_rows_to_show(self):
        return self.config_info["default_rows_to_show"]

    def get_color(self, color_name):
        return self.config_info["colors"][color_name]

    def get_font_name(self):
        return self.config_info["font_name"]

    def get_font_size(self):
        return self.config_info["font_size"]

    def get_background_path(self):
        return self.config_info["background_img_path"]

    def get_logo_path(self):
        return self.config_info["logo_path"]

    def get_bi_logo_path(self):
        return self.config_info["bi_logo_path"]


if __name__ == "__main__":
    app = WalletApp()
    app.run()
