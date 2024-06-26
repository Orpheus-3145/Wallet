import logging
import os
from datetime import date, datetime
from win32api import GetSystemMetrics
import win32com.client as win32         # per aprire applicazioni win
import pywintypes                       # per gestire alcune eccezioni legate al modulo di cui sopra

import Wallet
from AppExceptions import *

from kivy.config import Config

SETTINGS_INI = os.path.join(os.getcwd(), "..\\settings\\config_wallet.ini")
Config.read(SETTINGS_INI)

from kivy.lang import Builder
from Screens import *
from kivy.core.window import Window
from Popups import *


class BusIntApp:
    """App che permette di aprire un file di QlikView"""
    def __init__(self, bi_path):
        self.app = None             # applicazione di QlikView
        self.current_file = None    # istanza del file qlik
        if not os.path.exists(bi_path):
            raise AppException("Il file di BI {} non esiste".format(bi_path))
        elif os.path.splitext(bi_path)[1] != ".qvw":
            raise AppException("Il file di BI {} non ha estensione .qvw".format(bi_path))
        else:
            self.bi_path = os.path.dirname(bi_path)    # percorso del file qlik
            self.bi_name = os.path.basename(bi_path)   # nome del file qlik

    def open(self, user=None, pwd=None):
        try:
            self.app = win32.Dispatch('QlikTech.QlikView')
        except pywintypes.com_error as error:
            raise AppException(str(error))
        else:
            self.current_file = self.app.OpenDoc(os.path.join(os.getcwd(), self.bi_path, self.bi_name), user, pwd)
            return self.current_file

    def close(self):
        try:
            if self.current_file:
                self.current_file.CloseDoc()
            self.app.Quit()
        except AttributeError:      # se chiudo il file qlik prima dell'app ho queso errore, lo ignoro
            pass


class WalletApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stopped = False
        self.wallet_instance = None
        self.qlik_app = None
        self.config_info = {}
        self.stored_procs = {}
        self.read_config(Config)
        self.create_logger()
        logging.info("#" * 80)
        logging.info("app avviata")

    def read_config(self, config):
        try:
            self.config_info["kv_files"] = config["kivy_files"].values()
            self.config_info["dsn"] = config["database"]["dsn_name"].strip("'")
            self.config_info["bi_file_path"] = config["bi"]["bi_file_path"]
            self.config_info["backup_path"] = config["database"]["backup_path"]
            self.config_info["bi_logo_path"] = config["graphics"]["bi_logo_path"]
            self.config_info["background_img_path"] = config["graphics"]["background_img_path"]
            self.config_info["logo_path"] = config["graphics"]["logo_path"]
            self.config_info["log_path"] = config["log"]["log_path"]
            self.config_info["log_level"] = config.getint("log", "log_level")
            self.config_info["width_app"] = config.getint("graphics", "width")
            self.config_info["height_app"] = config.getint("graphics", "height")
            self.config_info["font_name"] = config["kivy"]["font_name"]
            self.config_info["font_size"] = config.getint("kivy", "font_size")
            self.config_info["max_rows_to_show"] = config.getint("widgets", "max_rows_to_show")  # max righe mostrate in SowMovementScreen
            self.config_info["default_rows_to_show"] = config.getint("widgets", "default_rows_to_show")  # default righe mostrate in SowMovementScreen
            self.config_info["colors"] = {}
            for item in self.config_info.keys():
                if item.endswith("_path") and os.path.exists(self.config_info[item]) is False:
                    raise AppException("file {} non trovato".format(self.config_info[item]))
            for color_rgba in config["colors"].keys():
                self.config_info["colors"][color_rgba] = Tools.str_to_list(config["colors"][color_rgba])
        except (KeyError, ValueError) as error:
            raise AppException("errore nel file .ini - trace: " + str(error))

    def create_logger(self):
        log_levels = {10: logging.DEBUG, 20: logging.INFO, 30: logging.WARNING, 40: logging.ERROR, 50: logging.CRITICAL}
        log_level = log_levels[self.config_info["log_level"]]
        log_name = "Logfile_{}.log".format(date.today().strftime("%d-%m-%Y"))
        log_path = self.config_info["log_path"]

        logger = logging.getLogger(__name__)
        logging.root = logger
        logger.setLevel(log_level)
        file_handler = logging.FileHandler(filename=os.path.join(log_path, log_name))
        log_formatter = logging.Formatter(fmt="%(asctime)s | %(levelname)-9s | %(message)s", datefmt='%m/%d/%Y %H:%M:%S')
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    def build(self):
        width_screen = GetSystemMetrics(0)
        height_screen = GetSystemMetrics(1)
        Window.left = (width_screen - self.config_info["width_app"]) // 2
        Window.top = (height_screen - self.config_info["height_app"]) // 2
        for kv_file in self.config_info["kv_files"]:
            if not os.path.exists(kv_file):
                logging.error("caricamento front-end - %s non trovato", kv_file)
                raise AppException("file di stile {} non trovato".format(kv_file))
            try:
                Builder.load_file(kv_file)
            except Exception as error:
                logging.error("caricamento front-end - errore in %s - %s", kv_file, str(error))
                raise AppException("caricamento front-end, errore: ".format(str(error)))
            logging.debug("caricamento front-end - %s letto", kv_file)
        return ManagerScreen()

    def connect(self):
        dsn = self.config_info["dsn"]
        try:
            logging.debug("connessione al database con dsn: %s", dsn)
            self.wallet_instance = Wallet.Wallet(dsn)
        except SqlError as db_err:
            logging.error("errore connessione - %s", str(db_err))
            raise AppException("Connessione al database fallita, consulta il log per ulteriori dettagli")
        else:
            logging.debug("connessione al database effettuata")
        bi_file = self.config_info["bi_file_path"]
        try:
            logging.debug("creazione app BI (pywin32) con file: %s", bi_file)
            self.qlik_app = BusIntApp(bi_file)
        except AppException as bi_error:
            logging.error("errore app BI (pywin32) - %s", str(bi_error))
            raise AppException("Errore app BI, consulta il log per ulteriori dettagli")
        else:
            logging.debug("app BI creata")

    def login(self, user, pwd, autologin):
        if autologin is True:
            self.connect()
            return True
        elif user == "" or pwd == "":
            raise AppException("Credenziali mancanti")
        self.connect()
        login_done = self.wallet_instance.login_wallet(user.strip(), pwd.strip())
        if login_done is True:
            logging.debug("utente %s ha effettuato l'accesso", user)
        return login_done

    def open_BI(self):
        try:
            user, pwd = self.wallet_instance.get_bi_credentials()
            self.qlik_app.open(user, pwd)
        except SqlError as db_err:
            logging.error("errore apertura BI - %s", str(db_err))
            raise AppException("Errore apertura BI, consulta il log per ulteriori dettagli")
        except AppException as bi_error:
            logging.error("errore apertura BI - %s", str(bi_error))
            raise AppException("Errore apertura BI, consulta il log per ulteriori dettagli")

    def insert_movement(self, id_mov, data_movement):
        try:
            logging.debug("inserimento nuovo movimento tipo: %s", id_mov)
            self.wallet_instance.insert_movement(id_mov=id_mov, data_info=data_movement)
        except (InternalError, SqlError) as int_err:
            logging.error("errore inserimento - %s", str(int_err))
            raise AppException("Movimento non inserito, consulta il log per ulteriori dettagli")
        else:
            logging.info("inserimento nuovo movimento tipo: %s riuscito", id_mov)

    def drop_records(self, list_records):
        count_errs = 0
        for record_to_drop in list_records:
            try:
                self.wallet_instance.drop_record(record_to_drop)
            except SqlError as error:
                logging.error("rimozione movimento id: %s fallita - %s", record_to_drop, str(error))
                count_errs = count_errs + 1
            else:
                logging.info("movimento id: %s rimosso", record_to_drop)
        if count_errs > 0:
            raise AppException("Errore nella rimozione record(s), consulta il log per ulteriori dettagli")

    def turn_deb_cred_into_mov(self, list_records):
        count_errs = 0
        for record_to_turn in list_records:
            try:
                self.wallet_instance.turn_deb_cred_into_mov(record_to_turn)
            except SqlError as error:
                logging.error("trasformazione deb/cred id: %s in movimento fallita - %s", record_to_turn, str(error))
                count_errs = count_errs + 1
            else:
                logging.info("deb/cred id: %s trasformato in movimento", record_to_turn)
        if count_errs > 0:
            raise AppException("Errore nella trasformazione record(s), consulta il log per ulteriori dettagli")

    def backup_database(self):
        backup_path = self.config_info["backup_path"]
        backup_name = "Wallet_{}.bak".format(datetime.now().strftime("%d-%m-%Y"))
        if not os.path.isabs(backup_path):
            backup_path = os.path.normpath(os.path.join(os.getcwd(), backup_path))
        for i in range(100):
            if not os.path.exists(os.path.join(backup_path, backup_name)):
                break
            backup_name = "Wallet_{}_{}.bak".format(datetime.now().strftime("%d-%m-%Y"), i)
        else:
            logging.error("più di 100 file di log uguali a %s in %s", backup_name, backup_path)
            raise AppException("Troppi file di log giornalieri esistenti in {}".format(backup_path))
        backup_path = os.path.join(backup_path, backup_name)
        try:
            self.wallet_instance.backup_database(backup_path)
        except SqlError as error:
            logging.error("creazione backup %s in %s fallita - %s", backup_name, backup_path, str(error))
            raise AppException("Backup fallito, consulta il log per ulteriori dettagli")
        else:
            logging.info("creato backup %s in %s", backup_name, backup_path)

    def on_stop(self):
        """Non è chiaro perchè ma il metodo app.stop() viene chiamato due volte, per evitare di scrivere due volte sul log
        utilizzo il parametro _stopped"""
        if not self._stopped:
            self._stopped = True
            if self.wallet_instance:
                self.wallet_instance.close_wallet()
            if self.qlik_app:
                self.qlik_app.close()
        logging.info("app chiusa")
        logging.info("#" * 80)

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

    def get_type_payments(self):
        try:
            return self.wallet_instance.get_info_db("pagamenti")
        except SqlError as db_err:
            logging.error(str(db_err))
            raise AppException("Errore database, consulta il log per ulteriori dettagli")

    def get_type_spec_movements(self):
        try:
            return self.wallet_instance.get_info_db("spese_varie")
        except SqlError as db_err:
            logging.error(str(db_err))
            raise AppException("Errore database, consulta il log per ulteriori dettagli")

    def get_type_entrate(self):
        try:
            return self.wallet_instance.get_info_db("entrate")
        except SqlError as db_err:
            logging.error(str(db_err))
            raise AppException("Errore database, consulta il log per ulteriori dettagli")

    def get_open_deb_creds(self):
        try:
            return self.wallet_instance.get_open_deb_creds()
        except SqlError as db_err:
            logging.error(str(db_err))
            raise AppException("Errore database, consulta il log per ulteriori dettagli")

    def get_last_n_records(self, id_mov, n_records):
        try:
            return self.wallet_instance.get_last_n_records(id_mov, n_records)
        except SqlError as db_err:
            logging.error(str(db_err))
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
