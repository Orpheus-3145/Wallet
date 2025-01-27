import logging
import os
from datetime import date
from dotenv import load_dotenv
from screeninfo import get_monitors

import Tools

from kivy.core.window import Window
from kivy.config import Config

PATH_ENV_FILE = Tools.get_abs_path("config/wallet.env")
load_dotenv(PATH_ENV_FILE)

PATH_KIVY_CONFIG = Tools.get_abs_path(os.getenv("PATH_KIVY_CONFIG", "config/wallet.ini"))
Config.read(PATH_KIVY_CONFIG)

from kivy.lang import Builder
from Screens import *
from Popups import *
from AppExceptions import *
import Wallet


class WalletApp(App):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._stopped = False
		self.wallet_instance = None
		self.config_info = {}
		self.read_config(Config)
		self.create_logger(self.config_info["log_path"], self.config_info["log_level"])

	def read_config(self, config):
		try:
			# generic env vars
			self.config_info["log_path"] = os.getenv("LOG_PATH", "logs/")
			self.config_info["log_level"] = int(os.getenv("LOG_LEVEL", "20"))
			self.config_info["backup_path"] = Tools.get_abs_path(os.getenv("PATH_BACKUP_DIR", "."))
			self.config_info["host"] = os.getenv("DB_HOST", "localhost")
			self.config_info["port"] = int(os.getenv("DB_PORT", "6543"))
			self.config_info["db_name"] = os.getenv("DB_NAME", "wallet")
			self.config_info["user"] = os.getenv("DB_USER")
			self.config_info["pwd"] = os.getenv("DB_USER_PWD")
			self.config_info["auth_mode"] = os.getenv("DB_AUTH_MODE", "scram-sha-256")
			# kivy data
			self.config_info["kivy_files"] = [Tools.get_abs_path(kv_file) for kv_file in config["kivy_files"].values()]
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
			raise AppException("Errore lettura config - trace: {}".format(str(error)))

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

	def connect(self, host_db='', port_db='', db_name='', user='', password='', auth_mode=''):
		self.wallet_instance = Wallet.Wallet(logging)
		if not db_name:
			db_name = self.config_info["db_name"]
		if not user:
			user = self.config_info["user"]
		if not password:
			password = self.config_info["pwd"]
		if not host_db:
			host_db = self.config_info["host"]
		if not port_db:
			port_db = self.config_info["port"]
		if not auth_mode:
			auth_mode = self.config_info["auth_mode"]
		try:
			self.wallet_instance.connect(user=user,
										password=password,
										auth_mode=auth_mode,
										host_db=host_db,
										port_db=port_db,
										db_name=db_name)
		except SqlError as db_err:
			self.update_log("errore connessione - %s", 40, str(db_err))
			raise AppException("Connessione al database fallita, consulta il log per ulteriori dettagli")
		else:
			self.update_log("connessione al database effettuata", 10)
		self.update_log("utente %s ha effettuato l'accesso", 20, user)

	def build(self):
		active_monitor = get_monitors()[0]
		Window.size = (self.config_info["width_app"], self.config_info["height_app"])
		Window.left = (active_monitor.width - self.config_info["width_app"]) // 2
		Window.top = (active_monitor.height - self.config_info["height_app"]) // 2
		
		for kv_file in self.config_info["kivy_files"]:
			try:
				Builder.load_file(kv_file)
			except Exception as error:
				self.update_log("caricamento front-end - errore in %s - %s", 40, kv_file, str(error))
				raise AppException("Caricamento front-end, errore: ".format(str(error)))
			self.update_log("caricamento front-end - %s", 10, kv_file)

		manager = ManagerScreen()
		Window.bind(on_key_down=manager.get_screen('login').enter_key_pressed)
		
		return manager

	def insert_movement(self, id_mov, data_movement):
		try:
			self.wallet_instance.insert_movement(id_mov=id_mov, data_info=data_movement)
		except (InternalError, SqlError) as error:
			self.update_log("errore interno - %s", 40, str(error))
			raise AppException("Errore interno, consulta il log per ulteriori dettagli")
		except WrongInputException as wrong_input:
			raise AppException(str(wrong_input))
		else:
			self.update_log("inserimento movimento tipo %s riuscito", 20, id_mov)

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
		try:
			self.wallet_instance.backup_database()
		except InternalError as error:
			self.update_log("creazione backup fallita - %s", 40, str(error))
			raise AppException("Backup fallito, consulta il log per ulteriori dettagli")
		else:
			self.update_log("creato backup in %s", 20, self.config_info["backup_path"])

	def drop_test_mov(self):
		try:
			self.wallet_instance.drop_test_mov()
		except InternalError as error:
			self.update_log("rimozione movimenti di test fallita - %s", 40, str(error))
			raise AppException("Eliminazione fallita, consulta il log per ulteriori dettagli")
		else:
			self.update_log("rimossi movimenti di test", 20)

	def on_stop(self):
		"""Non è chiaro perchè ma il metodo app.stop() viene chiamato due volte, per evitare di scrivere due volte sul log
		utilizzo il parametro _stopped"""
		if not self._stopped:
			self._stopped = True
			if self.wallet_instance:
				self.wallet_instance.disconnect_database()
		self.update_log("app chiusa", 20)
		self.update_log("#" * 80, 20)

	# db interrogations
	def get_movements(self, movs_to_drop=None):
		if movs_to_drop is None:
			movs_to_drop = []
		try:
			movements = self.wallet_instance.get_movements()
		except (SqlError, EmptySelectException) as db_err:
			self.update_log("errore database: %s", 40, str(db_err))
			raise AppException("Errore database, consulta il log per ulteriori dettagli")
		for mov_to_drop in movs_to_drop:
			for key_mov, name_mov in movements.items():
				if name_mov == mov_to_drop:
					del movements[key_mov]
					break
		return movements

	def get_type_accounts(self):
		try:
			return self.wallet_instance.get_map_data("conti")
		except (SqlError, EmptySelectException) as db_err:
			self.update_log("errore database: %s", 40, str(db_err))
			raise AppException("Errore database, consulta il log per ulteriori dettagli")

	def get_type_spec_movements(self):
		try:
			return self.wallet_instance.get_map_data("spese_varie")
		except (SqlError, EmptySelectException) as db_err:
			self.update_log("errore database: %s", 40, str(db_err))
			raise AppException("Errore database, consulta il log per ulteriori dettagli")

	def get_type_entrate(self):
		try:
			return self.wallet_instance.get_map_data("entrate")
		except (SqlError, EmptySelectException) as db_err:
			self.update_log("errore database: %s", 40, str(db_err))
			raise AppException("Errore database, consulta il log per ulteriori dettagli")

	def get_open_deb_creds(self):
		try:
			return self.wallet_instance.get_open_deb_creds()
		except (SqlError, EmptySelectException) as db_err:
			self.update_log("errore database: %s", 40, str(db_err))
			raise AppException("Errore database, consulta il log per ulteriori dettagli")

	def get_last_n_records(self, id_mov, n_records):
		try:
			return self.wallet_instance.get_last_n_records(id_mov, n_records)
		except (SqlError, InternalError) as db_err:
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


if __name__ == "__main__":
	app = WalletApp()
	app.run()
