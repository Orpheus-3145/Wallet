from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.factory import Factory

from MovLayouts import *
from DefaultLayouts import *
from Popups import *
from WalletApp import AppException


class ManagerScreen(ScreenManager):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._type_mov_dict = {}
        self.type_mov = ""
        self.add_widget(LoginScreen(name="login"))

    def create_screens(self):
        self.add_widget(MainScreen(name="main"))
        self.add_widget(InsertMovementScreen(name="insert"))
        self.add_widget(PayOffScreen(name="open_deb_cred"))
        self.add_widget(ShowMovementsScreen(max_rows_to_show=App.get_running_app().get_max_rows_to_show(),
                                            default_rows_to_show=App.get_running_app().get_default_rows_to_show(),
                                            name="show_movements"))

    def set_movements(self, movements):
        self._type_mov_dict = movements

    def get_type_mov(self):
        return self.type_mov

    def go_to_insert_screen(self, type_mov):
        if type_mov == "":  # quando torno nella schermata principale setto type_movement = "" in questo caso non mi serve alcun automatismo
            return
        self.type_mov = type_mov
        self.current = "insert"
        self.transition.direction = "left"

    def go_to_payoff_screen(self):
        self.current = "open_deb_cred"
        self.transition.direction = "up"

    def go_to_main_screen(self, direction="right"):
        self.type_mov = ""
        self.current = "main"
        self.transition.direction = direction


class LoginScreen(Screen):
    def login(self, username, password, autologin=False):
        login_status = True
        try:
            if autologin is False:
                login_status = App.get_running_app().login(username, password)
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            if login_status is False:
                Factory.SingleChoicePopup(info="Login fallito").open()
            else:
                self.manager.set_movements(App.get_running_app().get_movements())
                self.manager.create_screens()
                self.manager.go_to_main_screen()


class MainScreen(Screen):
    def on_kv_post(self, base_widget):      # NB move in a constructor?
        movements_list = App.get_running_app().get_movements(type_mov="general").values()
        self.ids.general_mov.update_layout(movements_list)

    def on_pre_enter(self, *args):
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
        self.manager.current = "show_movements"
        self.manager.transition.direction = "up"

    def open_bi(self):
        try:
            App.get_running_app().open_BI()
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()

    def set_movement(self, instance_btn):
        self.manager.go_to_insert_screen(instance_btn.text)

    def backup(self):
        try:
            App.get_running_app().backup_database()
        except Exception as err:
            Factory.ErrorPopup(err_text=str(err)).open()
        else:
            Factory.SingleChoicePopup(info="Backup creato con successo").open()


class InsertMovementScreen(Screen):
    def on_pre_enter(self):
        self.ids.mov_name.text = self.manager.get_type_mov().upper()
        self.add_widget(LayoutData(pos_hint={"x": .735, "y": .48}, size_hint=(.25, .28)))
        if self.manager.get_type_mov() != "Stipendio":
            self.add_widget(LayoutMainMov(type_payments=App.get_running_app().get_type_payments(),
                                          pos_hint={"x": .015, "y": .1},
                                          size_hint=[.35, .66]))
        if self.manager.get_type_mov() == "Spesa Generica":
            self.add_widget(LayoutSpesaGenerica(mov_list=App.get_running_app().get_type_spec_movements(),
                                                pos_hint={"x": .375, "y": .1},
                                                size_hint=[.35, .66]))
        elif self.manager.get_type_mov() == "Spesa Fissa":
            self.add_widget(LayoutSpesaFissa(pos_hint={"x": .375, "y": .64}, size_hint=(.35, 0.12)))
        elif self.manager.get_type_mov() == "Stipendio":
            self.add_widget(LayoutStipendio(pos_hint={"x": .375, "y": .1}, size_hint=(.35, .66)))
        elif self.manager.get_type_mov() == "Entrata":
            self.add_widget(LayoutEntrata(type_entrate=App.get_running_app().get_type_entrate(),
                                          pos_hint={"x": .375, "y": .29},
                                          size_hint=(.35, .47)))
        elif self.manager.get_type_mov() == "Debito - Credito":
            self.add_widget(LayoutDebitoCredito(pos_hint={"x": .375, "y": .4}, size_hint=(.35, .36)))
        elif self.manager.get_type_mov() == "Saldo Debito - Credito":
            pass
            # self.add_widget(LayoutSaldoDebitoCredito(type_payments=App.get_running_app().get_type_payments(),
            #                                          pos_hint={"x": .375, "y": .2},
            #                                          size_hint=(.35, .56)))
        elif self.manager.get_type_mov() == "Spesa di Mantenimento":
            self.add_widget(LayoutSpesaMantenimento(pos_hint={"x": .375, "y": .64}, size_hint=(.35, 0.12)))
        elif self.manager.get_type_mov() == "Spesa di Viaggio":
            self.add_widget(LayoutSpesaViaggio(pos_hint={"x": .375, "y": .52}, size_hint=(.35, .24)))
        else:
            raise AppException("unknown type mov: {type}".format(type=self.manager.get_type_mov()))

    def on_leave(self):
        App.get_running_app().main_mov_dict.clear()
        App.get_running_app().spec_mov_dict.clear()
        App.get_running_app().date_dict.clear()
        for layout in [layout for layout in self.children if isinstance(layout, DefaultLayout)]:
            self.remove_widget(layout)

    def interrupt_insertion(self):
        if App.get_running_app().main_mov_dict != {} or App.get_running_app().spec_mov_dict != {}:
            Factory.DoubleChoicePopup(info="Esci senza inserire il movimento?", func_to_exec=self.manager.go_to_main_screen).open()
        else:
            self.manager.go_to_main_screen()

    def insert_movement(self):
        try:
            App.get_running_app().insert_movement()
        except Exception as error:
            Factory.ErrorPopup(err_text=str(error)).open()
        else:
            Factory.SingleChoicePopup(info="MOVIMENTO INSERITO", func_to_exec=self.manager.go_to_main_screen).open()


class PayOffScreen(Screen):
    """Schermata per gestire la selezione di uno o più debiti/crediti, essi possono essere eliminati o saldati
    chiamando lo screen InsertMovementScreen; nb: è possibile fare saldi (o rimozioni) multipli, il segno finale
    della somma determinerà se si tratta di una spesa o di un'entrata"""
    selected_ids = []  # lista degli id dei record selezionati da eliminare o da saldare, NB mettere membro non static

    def on_pre_enter(self):
        """Ogni volta che entro nello screen aggiorno la tabella visualizzata"""
        self.update_rows()
        self.ids.appearing_box.hide_widget()

    def on_leave(self, *args):
        """Ogni volta che abbandono lo screen svuoto la tabella e nascondo il bottone di saldo debito/credito"""
        self.selected_ids.clear()                       # cancello gli id dei record selezionati
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
        App.get_running_app().spec_mov_dict["ID_PREV_DEB_CRED"] = list(self.selected_ids)
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
        list_movements = App.get_running_app().get_movements(type_mov="general").values()       # lista dei possibili movimenti da selezionare
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
