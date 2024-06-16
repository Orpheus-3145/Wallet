from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.factory import Factory

from MovLayouts import *


class ManagerScreen(ScreenManager):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(LoginScreen(name="login"))

    def create_screens(self):
        self.add_widget(MainScreen(name="main"))
        self.add_widget(InsertMovementScreen(name="insert"))
        self.add_widget(PayOffScreen(name="open_deb_cred"))
        self.add_widget(ShowMovementsScreen(max_rows_to_show=App.get_running_app().get_max_rows_to_show(),
                                            default_rows_to_show=App.get_running_app().get_default_rows_to_show(),
                                            name="show_movements"))

    def go_to_insert_screen(self, type_mov):
        self.get_screen("insert").set_current_mov(type_mov)
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
        username = self.ids.input_user.text.strip()
        password = self.ids.input_pwd.text.strip()
        try:
            login_status = App.get_running_app().login(username, password, autologin)
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            if login_status is False:
                Factory.SingleChoicePopup(info="Login fallito").open()
            else:
                self.manager.create_screens()
                self.manager.go_to_main_screen()


class MainScreen(Screen):
    def on_pre_enter(self, *args):
        movements_list = App.get_running_app().get_movements(type_mov="general")
        self.ids.general_mov.update_layout(movements_list)
        self.ids.deb_cred.hide_widget()
        self.ids.general_mov.hide_widget()

    def show_movements(self):
        """Attiva il layout per visualizzare i tipi di moviemento generici"""
        self.ids.general_mov.show_widget()
        self.ids.deb_cred.hide_widget()

    def show_deb_cred(self):
        """Attiva il layout per visualizzare i tipi di movimento deb/cred"""
        self.ids.deb_cred.show_widget()
        self.ids.general_mov.hide_widget()

    def show_last_movements(self):
        """Va allo screen ShowMovementsScreen"""

    def open_bi(self):
        try:
            App.get_running_app().open_BI()
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()

    def insert_new_movement(self, btn_instance):
        self.manager.go_to_insert_screen(btn_instance.text)

    def backup(self):
        try:
            App.get_running_app().backup_database()
        except Exception as err:
            Factory.ErrorPopup(err_text=str(err)).open()
        else:
            Factory.SingleChoicePopup(info="Backup creato con successo").open()


class InsertMovementScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.current_mov = ""
        self.data_layouts = {"date": self.ids.layout_date,
                             "main": self.ids.layout_main,
                             "Spesa Generica": self.ids.layout_s_varia,
                             "Spesa Fissa": self.ids.layout_s_fissa,
                             "Stipendio": self.ids.layout_stipendio,
                             "Entrata": self.ids.layout_entrata,
                             "Debito - Credito": self.ids.layout_deb_cred,
                             "Spesa di Mantenimento": self.ids.layout_s_mantenimento,
                             "Spesa di Viaggio": self.ids.layout_data_s_viaggio}
        for layout in self.data_layouts.values():
            layout.hide_widget()
        self.ids_deb_cred = {}

    def set_current_mov(self, current_mov):
        self.current_mov = current_mov

    def on_pre_enter(self):
        self.ids.mov_name.text = self.current_mov.upper()
        self.data_layouts["date"].show_widget()
        self.data_layouts["date"].refresh_data()
        self.data_layouts["main"].show_widget()
        self.data_layouts["main"].refresh_data(App.get_running_app().get_type_payments())
        if self.current_mov != "Saldo Debito - Credito":
            self.data_layouts[self.current_mov].show_widget()
            if self.current_mov == "Spesa Generica":
                self.data_layouts[self.current_mov].refresh_data(App.get_running_app().get_type_spec_movements())
            elif self.current_mov == "Entrata":
                self.data_layouts[self.current_mov].refresh_data(App.get_running_app().get_type_entrate())
            else:
                self.data_layouts[self.current_mov].refresh_data()
        else:
            self.ids_deb_cred = self.manager.get_screen("open_deb_cred").get_ids()

    def on_leave(self):
        if self.current_mov != "Saldo Debito - Credito":
            self.data_layouts[self.current_mov].hide_widget()

    def insert_movement(self):
        movement_data = self.data_layouts["date"].get_data()
        movement_data.update(self.data_layouts["main"].get_data())
        if self.current_mov == "Saldo Debito - Credito":
            movement_data.update({"id_saldo_deb_cred": Tools.list_to_str(self.ids_deb_cred)})
        else:
            movement_data.update(self.data_layouts[self.current_mov].get_data())
        try:
            App.get_running_app().insert_movement(self.current_mov, movement_data)
        except Exception as error:
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
        """Aggiorna i record della tabella e i nomi dei campi leggendoli dal db"""
        self.selected_ids.clear()
        try:
            cols, rows = App.get_running_app().wallet_instance.get_open_deb_creds()
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            deb_cred_box_col = self.ids.deb_cred_columns        # contenitore dei vari nomi di colonna
            deb_cred_view = self.ids.deb_cred_tab               # tabella dei record
            deb_cred_box_col.update_layout(cols)                # aggiorno i due widget
            deb_cred_view.update_layout(rows)

    def add_new_id(self, btn_instance):
        """Aggiunge un nuovo id di movimento da saldare alla lista in spec_mov_dict o lo rimuove se già presente,
            gestisce poi la comparsa o meno del bottone SALDA/ELIMINA a seconda del fatto che tale lista sia vuota o
            meno"""
        id_record = btn_instance.parent_layout.id_record
        if id_record not in self.selected_ids:      # se non c'è, aggiungo l'id e visualizzo il btn SALDA/RIMUOVI
            self.selected_ids.append(id_record)
        else:                                       # in caso contrario lo rimuovo
            self.selected_ids.remove(id_record)
        if not self.selected_ids:                   # se la lista è vuota faccio sparire il bottone
            self.ids.appearing_box.hide_widget()
        else:                                       # in caso contrario lo faccio apparire
            self.ids.appearing_box.show_widget()

    def go_to_insert_screen(self):
        self.manager.go_to_insert_screen("Saldo Debito - Credito")    # vado allo screen InsertMovementScreen

    def remove_records(self):
        """Rimuove i record (cioè i movimenti), aggiorna la tabella e nasconde il box per la rimozione dei record
        selezionati"""
        try:
            App.get_running_app().drop_records(self.selected_ids, "Debito - Credito")
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            self.update_rows()
            self.ids.appearing_box.hide_widget()

    def turn_deb_cred_into_mov(self):
        try:
            App.get_running_app().turn_deb_cred_into_mov(self.selected_ids)
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            self.update_rows()
            self.ids.appearing_box.hide_widget()


class ShowMovementsScreen(Screen):
    def __init__(self, max_rows_to_show, default_rows_to_show, **kw):
        super().__init__(**kw)
        self.type_movement = ""                 # tipo di movimento scelto da esporre
        self._selected_records_to_show = True   # flag t/f se ho impostato quante righe visualizzare (di default è sempre valorizzato)
        self._selected_movement = False         # flag t/f se ho selezionato il movimento
        self.records_to_drop = []               # lista contenente gli id dei record da eliminare
        self.max_rows_to_show = max_rows_to_show
        self.current_rows_shown = default_rows_to_show

    def on_pre_enter(self):
        """Quando entro nello screen aggiorno il layout contenete i tipi di movimenti (entrata, spesa generica, ...) da
        visionare"""
        self.ids.info_no_rows.text = "Record visualizzati [max: {}]".format(self.max_rows_to_show)
        self.ids.input_no_rows.text = str(self.current_rows_shown)
        list_movements = App.get_running_app().get_movements(type_mov="general")       # lista dei possibili movimenti da selezionare
        self.ids.box_movements.update_layout(list_movements)                      # aggiorno il relativo layout
        self.ids.remove_record_btn.hide_widget()

    def on_leave(self):
        self.type_movement = ""                     # movimento scelto
        self.records_to_drop.clear()                # svuoto la lista di eventuali record selezionati
        self.ids.mov_columns.clear_widgets()        # svuoto il contenitore dei nomi dei campi
        self.ids.rows_box.clear_widgets()           # svuoto la tabella
        self.ids.box_movements.clear_widgets()      # svuoto il contenitore dei movimenti
        self.ids.remove_record_btn.hide_widget()    # faccio sparire il bottone per rimuovere i record

    def set_new_number(self, new_number):
        try:
            self.current_rows_shown = int(new_number)
            if self.current_rows_shown < 0:
                raise ValueError()
        except ValueError:
            self.ids.info_no_rows.text = "[color=cb4335][i]non valido[/i][/color]"
            self._selected_records_to_show = False
        else:
            self.ids.info_no_rows.text = "Record visualizzati [max: {}]".format(self.max_rows_to_show)
            if self.current_rows_shown > self.max_rows_to_show:  # per evitare troppi rallentamenti
                self.current_rows_shown = self.max_rows_to_show
                self.ids.input_no_rows.text = str(self.max_rows_to_show)
            self._selected_records_to_show = True
            if self._selected_movement is True:  # la tabella è già attiva, la aggiorno
                self.update_rows()

    def set_movement(self, btn_instance):
        self.type_movement = btn_instance.text
        self._selected_movement = True
        self.records_to_drop.clear()
        self.ids.remove_record_btn.hide_widget()
        if self._selected_records_to_show is True:
            self.update_rows()

    def update_rows(self):
        self.records_to_drop.clear()                # svuoto eventuali id selezionati in precedenza
        field_name_box = self.ids.mov_columns       # box contenente i nomi dei campi
        rows_box = self.ids.rows_box                # tabella contenente i vari record
        try:
            col_names, rows = App.get_running_app().wallet_instance.get_last_n_records(self.current_rows_shown, self.type_movement)
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            field_name_box.update_layout(col_names)     # aggiorno l'header (i.e. nomi dei campi)
            rows_box.update_layout(rows)                # aggiorno la tabella

    def add_record_to_remove(self, btn_instance):
        """Aggiunge/rimuove l'id corrispondente alla riga selezionata nella tabella, di conseguenza attiva/disattiva
        il bottone a comparsa che permette di rimuovere i record selezionati"""
        id_record = btn_instance.parent_layout.id_record
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
            App.get_running_app().drop_records(self.records_to_drop, self.type_movement)
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            self.update_rows()
            self.ids.remove_record_btn.hide_widget()
