import logging
import os
from datetime import date
from win32api import GetSystemMetrics
import Wallet
# import Tools

from kivy.config import Config

SETTINGS_INI = os.path.join(os.getcwd(), "..\\settings\\config_wallet.ini")
Config.read(SETTINGS_INI)

from kivy.lang import Builder
from Screens import *
from kivy.core.window import Window
from Popups import *


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
        self._stopped = False
        self.wallet_instance = None
        self.qlik_app = None
        self.config_info = {}
        self.read_config(Config)
        self.create_logger()
        self.stored_procs = {}

    def read_config(self, config):
        log_levels = {10: logging.DEBUG, 20: logging.INFO, 30: logging.WARNING, 40: logging.ERROR, 50: logging.CRITICAL}
        try:
            self.config_info["kv_files"] = config["kivy_files"].values()
            self.config_info["bi_file_path"] = config["bi"]["bi_file_path"]
            self.config_info["backup_path"] = config["database"]["backup_path"]
            self.config_info["bi_logo_path"] = config["graphics"]["bi_logo_path"]
            self.config_info["background_img_path"] = config["graphics"]["background_img_path"]
            self.config_info["logo_path"] = config["graphics"]["logo_path"]
            self.config_info["log_path"] = config["log"]["log_path"]
            for item in self.config_info.keys():
                if item.endswith("_path") and os.path.exists(self.config_info[item]) is False:
                    raise AppException("file {} non trovato".format(self.config_info[item]))
            self.config_info["dsn"] = config["database"]["dsn_name"].strip("'")
            self.config_info["log_name"] = config["log"]["log_name"]
            self.config_info["log_format"] = config["log"]["log_format"]
            self.config_info["log_level"] = log_levels[config.getint("log", "log_level")]
            self.config_info["width_app"] = config.getint("graphics", "width")
            self.config_info["height_app"] = config.getint("graphics", "height")
            self.config_info["font_name"] = config["kivy"]["font_name"]
            self.config_info["font_size"] = config.getint("kivy", "font_size")
            self.config_info["max_rows_to_show"] = config.getint("widgets", "max_rows_to_show")  # max righe mostrate in SowMovementScreen
            self.config_info["default_rows_to_show"] = config.getint("widgets", "default_rows_to_show")  # default righe mostrate in SowMovementScreen
            self.config_info["colors"] = {}
            for color_rgba in config["colors"].keys():
                self.config_info["colors"][color_rgba] = Tools.str_to_list(config["colors"][color_rgba])
        except (KeyError, ValueError) as error:
            raise AppException("errore nel file .ini - trace: " + str(error))

    def create_logger(self):
        logger = logging.getLogger(self.config_info["log_name"])
        logging.root = logger
        logger.setLevel(self.config_info["log_level"])
        log_path = self.config_info["log_path"]
        log_name = self.config_info["log_name"].format(date.today().strftime("%d-%m-%Y"))
        file_handler = logging.FileHandler(filename=os.path.join(log_path, log_name))
        log_formatter = logging.Formatter(fmt=self.config_info["log_format"])
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(self.config_info["log_level"])
        logger.addHandler(file_handler)
        logging.info("[%-10s]: %s", "WalletApp", "#" * 80)

    def build(self):
        width_screen = GetSystemMetrics(0)
        height_screen = GetSystemMetrics(1)
        Window.left = (width_screen - self.config_info["width_app"]) // 2
        Window.top = (height_screen - self.config_info["height_app"]) // 2
        for kv_file in self.config_info["kv_files"]:
            if not os.path.exists(kv_file):
                logging.error("[%-10s]: avvio app errore - file %s non trovato", "WalletApp", kv_file)
                raise AppException("file .kv %s non trovato" + kv_file)
            try:
                Builder.load_file(kv_file)
            except Exception as error:
                logging.error("[%-10s]: avvio app - errore file %s - trace: %s", "WalletApp", kv_file, str(error))
                raise AppException(str(error))
        logging.info("[%-10s]: avvio app - caricati i file di stile .kv, creato ScreenManager e Screen di login" % "WalletApp")
        return ManagerScreen()

    def connect(self):
        self.wallet_instance = Wallet.Wallet(self.config_info["dsn"])
        self.qlik_app = Wallet.QlikViewApp(self.config_info["bi_file_path"])

    def login(self, user, pwd, autologin):
        if autologin is True:
            self.connect()
            return True
        elif user == "" or pwd == "":
            raise AppException("Credenziali mancanti")
        self.connect()
        return self.wallet_instance.login_wallet(user.strip(), pwd.strip())

    def open_BI(self):
        user, pwd = self.wallet_instance.get_bi_credentials()
        self.qlik_app.open(user, pwd)

    def insert_movement(self, id_mov, data_movement):
        self.wallet_instance.insert_movement(id_mov=id_mov, data_info=data_movement)

    def drop_records(self, list_records):
        for record_to_drop in list_records:
            self.wallet_instance.drop_record(record_to_drop)

    def turn_deb_cred_into_mov(self, list_records):
        self.wallet_instance.turn_deb_cred_into_mov(list_records)

    def backup_database(self):
        """Crea un backup del database al percorso inserito nel file .ini, il formato del nome del backup viene
        stabilito più a basso livello (metodo Wallet.backup_database)"""
        self.wallet_instance.backup_database(self.config_info["backup_path"])

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

    def get_max_rows_to_show(self):
        return self.config_info["max_rows_to_show"]

    def get_default_rows_to_show(self):
        return self.config_info["default_rows_to_show"]

    def get_movements(self, get_all=False):
        return self.wallet_instance.get_movements(get_all)

    def get_type_payments(self):
        return self.wallet_instance.get_info_db("pagamenti")

    def get_type_spec_movements(self):
        return self.wallet_instance.get_info_db("spese_varie")

    def get_type_entrate(self):
        return self.wallet_instance.get_info_db("entrate")

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
