from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.app import App
import Tools

from MovLayouts import *


class ManagerScreen(ScreenManager):
	def __init__(self, **kw):
		super().__init__(**kw)
		self.add_widget(LoginScreen(name="login"))

	def create_screens(self):
		try:
			db_movs = App.get_running_app().get_movements()
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.add_widget(MainScreen(name="main"))
			self.add_widget(InsertMovementScreen(movements=db_movs, name="insert"))
			self.add_widget(PayOffScreen(name="open_deb_cred"))
			self.add_widget(ShowMovementsScreen(max_rows_to_show=App.get_running_app().get_max_rows_to_show(),
												default_rows_to_show=App.get_running_app().get_default_rows_to_show(),
												name="show_movements"))

	def go_to_insert_screen(self, id_mov):

		self.get_screen("insert").set_id_mov(id_mov)
		self.current = "insert"
		self.transition.direction = "left"

	def go_to_payoff_screen(self):
		self.current = "open_deb_cred"
		self.transition.direction = "up"

	def go_to_show_movements_screen(self):
		self.current = "show_movements"
		self.transition.direction = "up"

	def go_to_main_screen(self, direction="right"):
		self.current = "main"
		self.transition.direction = direction


class LoginScreen(Screen):
	def login(self, autologin=False):
		if autologin is True:
			username, password = "fra", "91913881"
		else:
			username = self.ids.input_user.text.strip()
			password = self.ids.input_pwd.text.strip()
		if autologin == False and (not username or not password):
			Factory.ErrorPopup(err_text="Credenziali mancanti").open()
			return
		try:
			login_status = App.get_running_app().connect(username, password)
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			# if login_status is False:
			#     Factory.ErrorPopup(err_text="Login fallito").open()
			# else:
			self.manager.create_screens()
			self.manager.go_to_main_screen()


class MainScreen(Screen):
	def on_pre_enter(self):
		try:
			mov_list = App.get_running_app().get_movements(movs_to_drop=["Saldo Debito - Credito"])
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.ids.general_mov.update_layout(mov_list)
			self.ids.general_mov.hide_widget()

	def show_movements(self):
		"""Attiva il layout per visualizzare i tipi di moviemento generici"""
		self.ids.general_mov.show_widget()

	def set_movement(self, new_id_mov):
		self.manager.go_to_insert_screen(new_id_mov)

	def backup(self):
		try:
			App.get_running_app().backup_database()
		except AppException as err:
			Factory.ErrorPopup(err_text=str(err)).open()
		else:
			Factory.SingleChoicePopup(info="Backup creato con successo").open()


class InsertMovementScreen(Screen):
	def __init__(self, movements, **kw):
		super().__init__(**kw)
		self.id_mov = -1
		self.movements = movements          # dict {id_mov: name_mov}
		self.ids_deb_cred = []
		self.data_layouts = {1: self.ids.layout_s_varia,
							 2: self.ids.layout_s_fissa,
							 3: self.ids.layout_stipendio,
							 4: self.ids.layout_entrata,
							 5: self.ids.layout_deb_cred,       # NB no 6th! there's no layout for type 6
							 7: self.ids.layout_s_mantenimento,
							 8: self.ids.layout_data_s_viaggio}
		for layout in self.data_layouts.values():
			layout.hide_widget()

	def set_id_mov(self, id_mov):
		self.id_mov = id_mov

	def on_pre_enter(self):
		if self.id_mov not in self.movements:
			if self.id_mov == -1:
				App.get_running_app().update_log("internal app fault - ID movimento non settato [metodo set_current_mov() non chiamato]", 50)
			else:
				App.get_running_app().update_log("internal app fault - ID movimento non esistente", 50)
			Factory.ErrorPopup(err_text="errore interno, consulta log per ulteriori dettagli", func_to_exec=self.manager.go_to_main_screen).open()
			return
		self.ids.mov_name.text = self.movements[self.id_mov]
		self.ids.layout_date.refresh_data()
		self.ids.layout_main.refresh_data()
		if self.movements[self.id_mov] == "Saldo Debito - Credito":
			self.ids_deb_cred = self.manager.get_screen("open_deb_cred").get_ids()
		else:
			self.data_layouts[self.id_mov].refresh_data()
			self.data_layouts[self.id_mov].show_widget()

	def on_leave(self):
		if self.id_mov in self.movements:
			if self.movements[self.id_mov] == "Saldo Debito - Credito":
				self.ids.layout_main.show_widget()
			else:
				self.data_layouts[self.id_mov].hide_widget()
			self.id_mov = -1

	def insert_movement(self):
		try:
			movement_data = self.ids.layout_date.get_data()
			movement_data.update(self.ids.layout_main.get_data())

			if self.movements[self.id_mov] == "Saldo Debito - Credito":
				movement_data.update({"id_saldo_deb_cred": Tools.list_to_str(self.ids_deb_cred)})
			else:
				movement_data.update(self.data_layouts[self.id_mov].get_data())
			
			App.get_running_app().insert_movement(self.id_mov, movement_data)

		except (AppException, WrongInputException) as error:
			Factory.ErrorPopup(err_text=str(error)).open()
	
		else:
			Factory.SingleChoicePopup(info="MOVIMENTO INSERITO", func_to_exec=self.manager.go_to_main_screen).open()


class PayOffScreen(Screen):
	def __init__(self, **kw):
		super().__init__(**kw)
		self.selected_ids = []  # lista degli id dei record selezionati da eliminare o da saldare

	def get_ids(self):
		return self.selected_ids

	def on_pre_enter(self):
		"""Ogni volta che entro nello screen aggiorno la tabella visualizzata"""
		self.update_rows()
		self.ids.appearing_box.hide_widget()

	def on_leave(self, *args):
		"""Ogni volta che abbandono lo screen svuoto la tabella e nascondo il bottone di saldo debito/credito"""
		self.ids.deb_cred_columns.clear_widgets()       # svuoto i nomi dei campi letti
		self.ids.deb_cred_tab.clear_widgets()           # svuoto la tabella
		self.ids.appearing_box.hide_widget()           # faccio sparire il box di eliminazione/saldo

	def update_rows(self):
		try:
			cols, rows = App.get_running_app().get_open_deb_creds()
		except AppException as err:
			Factory.ErrorPopup(err_text=str(err)).open()
		else:
			self.selected_ids.clear()
			self.ids.deb_cred_columns.update_layout(cols)
			self.ids.deb_cred_tab.update_layout(rows)

	def add_new_id(self, id_record):
		"""Aggiunge un nuovo id di movimento da saldare alla lista in spec_mov_dict o lo rimuove se già presente,
			gestisce poi la comparsa o meno del bottone SALDA/ELIMINA a seconda del fatto che tale lista sia vuota o
			meno"""
		if id_record not in self.selected_ids:      # se non c'è, aggiungo l'id e visualizzo il btn SALDA/RIMUOVI
			self.selected_ids.append(id_record)
		else:                                       # in caso contrario lo rimuovo
			self.selected_ids.remove(id_record)
		if not self.selected_ids:                   # se la lista è vuota faccio sparire il bottone
			self.ids.appearing_box.hide_widget()
		else:                                       # in caso contrario lo faccio apparire
			self.ids.appearing_box.show_widget()

	def go_to_insert_screen(self):
		self.manager.go_to_insert_screen(6)

	def remove_records(self):
		"""Rimuove i record (cioè i movimenti), aggiorna la tabella e nasconde il box per la rimozione dei record
		selezionati"""
		try:
			App.get_running_app().drop_records(self.selected_ids)
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.update_rows()
			self.selected_ids.clear()
			self.ids.appearing_box.hide_widget()

	def turn_deb_cred_into_mov(self):
		try:
			App.get_running_app().turn_deb_cred_into_mov(self.selected_ids)
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.update_rows()
			self.ids.appearing_box.hide_widget()


class ShowMovementsScreen(Screen):
	def __init__(self, max_rows_to_show, default_rows_to_show, **kw):
		super().__init__(**kw)
		self.max_rows_to_show = max_rows_to_show
		self.current_rows_shown = default_rows_to_show
		self.curr_mov_id = -1                   # movimento corrente selzionato
		self.records_to_drop = []               # lista contenente gli id dei record da eliminare

	def on_pre_enter(self):
		"""Quando entro nello screen aggiorno il layout contenete i tipi di movimenti (entrata, spesa generica, ...) da
		visionare"""
		try:
			mov_list = App.get_running_app().get_movements(movs_to_drop=["Debito - Credito", "Saldo Debito - Credito"])
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.ids.info_no_rows.text = "Record visualizzati [max: {}]".format(self.max_rows_to_show)
			self.ids.input_no_rows.text = str(self.current_rows_shown)
			self.ids.box_movements.update_layout(mov_list)
			self.ids.remove_record_btn.hide_widget()
			self.ids.refresh_mov_btn.hide_widget()
			self.curr_mov_id = -1

	def on_leave(self):
		self.ids.mov_columns.clear_widgets()        # svuoto il contenitore dei nomi dei campi
		self.ids.rows_box.clear_widgets()           # svuoto la tabella
		self.ids.remove_record_btn.hide_widget()    # faccio sparire il bottone per rimuovere i record
		self.records_to_drop.clear()                # svuoto la lista di eventuali record selezionati
		self.ids.refresh_mov_btn.hide_widget()
		self.curr_mov_id = -1

	def set_new_number(self, new_number):
		try:
			self.current_rows_shown = int(new_number)
			if self.current_rows_shown <= 0:
				raise ValueError()
		except ValueError:
			self.ids.info_no_rows.text = "[color=cb4335][i]non valido[/i][/color]"
			self.current_rows_shown = -1
		else:
			self.ids.info_no_rows.text = "Record visualizzati [max: {}]".format(self.max_rows_to_show)
			if self.current_rows_shown > self.max_rows_to_show:
				self.current_rows_shown = self.max_rows_to_show
				self.ids.input_no_rows.text = str(self.max_rows_to_show)
			self.ids.refresh_mov_btn.show_widget()

	def set_movement(self, new_id_mov):
		self.curr_mov_id = new_id_mov
		self.records_to_drop.clear()
		self.ids.remove_record_btn.hide_widget()
		self.ids.refresh_mov_btn.show_widget()

	def update_rows(self):
		try:
			if self.current_rows_shown == -1 or self.curr_mov_id == -1:
				App.get_running_app().update_log("parametri invalidi per interrogazione db, n records: %s, id tipo mov: %s", 50, self.current_rows_shown, self.curr_mov_id)
				Factory.ErrorPopup(err_text="errore interno, consulta log per ulteriori dettagli").open()
				return
			col_names, rows = App.get_running_app().get_last_n_records(self.curr_mov_id, self.current_rows_shown)
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.ids.mov_columns.update_layout(col_names)
			self.ids.rows_box.update_layout(rows)
			self.ids.refresh_mov_btn.hide_widget()

	def add_record_to_remove(self, id_record):
		"""Aggiunge/rimuove l'id corrispondente alla riga selezionata nella tabella, di conseguenza attiva/disattiva
		il bottone a comparsa che permette di rimuovere i record selezionati"""
		if id_record not in self.records_to_drop:
			self.records_to_drop.append(id_record)
		else:
			self.records_to_drop.remove(id_record)
		if not self.records_to_drop:  # se la lista è vuota rendo invisibile il bottone per eliminare i record
			self.ids.remove_record_btn.hide_widget()
		else:
			self.ids.remove_record_btn.show_widget()

	def remove_records(self):
		try:
			App.get_running_app().drop_records(self.records_to_drop)
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.update_rows()
			self.records_to_drop.clear()
			self.ids.remove_record_btn.hide_widget()


if __name__ == "__main__":
	pass