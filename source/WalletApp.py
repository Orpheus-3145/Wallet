import Wallet
import Tools
import logging
from kivy.config import Config

Config.read("settings\\config_wallet.ini")
Tools.set_center_app(Config)


def modify_config_kivy_file():
    """Modifica il file ini config_wallet.ini che viene letto alla riga precedente, decommentare per fare delle ulteriori
    modifiche non manuali"""
    # la dimensione max dell'app è 720x1280 per PC Dell
    # la dimensione max dell'app è 1920x1080 per PC fisso
    # modificare e decommentare per cambiare la configurazione
    # Config.set("kivy", "log_enable", 0)
    # Config.set("graphics", "fullscreen", 0)       # "0" per settare manualmente h/w e left/top, "auto" per fullscreen
    # Config.set("graphics", "borderless", 1)
    # Config.set("graphics", "height", 576)  # -20%
    # Config.set("graphics", "width", 1024)  # -20%
    # Config.set("graphics", "position", "custom")
    # Config.set("graphics", "top", 72)               # 252 PC Fisso
    # Config.set("graphics", "left", 128)             # 448 PC Fisso
    # Config.set("graphics", "window_state", "visible")  # da chiarire
    # Config.set("graphics", "resizable", 1)
    # Config["kivy_files"] = {"Screens": "C:\\My Documents\\Informatica\\Python\\WALL€T\\Wallet\\kv\\Screens.kv",
    #                         "Movements": "C:\\My Documents\\Informatica\\Python\\WALL€T\\Wallet\\kv\\Movements.kv",
    #                         "MyDefaultWidget": "C:\\My Documents\\Informatica\\Python\\WALL€T\\Wallet\\kv\\MyDefaultWidgets.kv"}

    # Config["kivy_data"] = {"font": "C:\\My Documents\\Informatica\\Python\\WALL€T\\font\\militech\\militech_r_2019-04-13.ttf",
    #                        "background_image": "C:\\My Documents\\Informatica\\Python\\WALL€T\\logos\\3169475.jpg",
    #                        "logo_image": "C:\\My Documents\\Informatica\\Python\\WALL€T\\\\logos\\W_logo_3.jpg"}

    # Config["kivy_colors"] = {"ORANGE_RGBA": [248 / 255, 157 / 255, 14 / 255, 1],
    #                         "BLUE_RGBA": [23 / 255, 40 / 255, 150 / 255, 1],
    #                         "GREY_RGBA": [35 / 255, 31 / 255, 32 / 255, 1],
    #                         "LIGHTGREY_RGBA": [118 / 255, 118 / 255, 118 / 255, 1],
    #                         "DARKGREY_RGBA": [60 / 255, 60 / 255, 60 / 255, 1],
    #                         "GREEN_RGBA": [144 / 255, 1, 0, 1],
    #                         "LOWGREEN_RGBA": [144 / 255, 1, 0, 0.75],
    #                         "NORMGREEN_RGBA": [53 / 255, 238 / 255, 24 / 255, 1],
    #                         "LIGHTNORMGREEN_RGBA": [0 / 255, 1, 12 / 255, 1],
    #                         "RED_RGBA": [1, 57 / 255, 43 / 255, 1]}
    # Config["log"] = {"path_log_file": "C:\\My Documents\\Informatica\\Python\\WALL€T\\logs",
    #                  "name_log_file": "Logfile_%s.log" % date.today().strftime("%d-%m-%Y"),
    #                  "foormat_log_file": "%(asctime)s | %(levelname)s | %(message)s"}
    # Config["log"]["level"] = "20"

    # Config["bi"] = {"path_qlik_file": "C:\\My Documents\\Informatica\\Python\\WALL€T\\Qlik\\WALLET.qvw"}
    # Config["dsn"] = {"dsn_name": "DSN=WALLET;Trusted_connection=yes"}

    Config.write()


# modify_config_kivy_file()


from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import ObjectProperty

# widget
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView


log_levels = {10: logging.DEBUG, 20: logging.INFO, 30: logging.WARNING, 40: logging.ERROR, 50: logging.CRITICAL}


class AppException(Exception):
    """Se si verifica un errore interno a livello di funzionamento di widget"""
    def __init__(self, error_text):
        self.error_text = error_text  # creo la proprietà di classe per avere maggiori informazioni sull'errore verificatosi
        super().__init__()

    def __str__(self):
        return self.error_text


# Screen e ScreenManager
class ManagerScreen(ScreenManager):
    """Gestore delle varie schermate dell'app, le prime 2 ('access' e 'login') vengono aggiunte dal metodo app.build(),
    poi se il login va a buon fine viene creata la schermata 'main'
    - type_mov -> è il tipo di spesa/entrata che si sta inserendo, il cambiare il suo valore genera la creazione e
        spostamento nella schermata relativa alla scelta fatta
    - _type_mov_dict -> dizionario di tutti i movimenti possibili, popolato una volta che l'app è connessa al db"""
    type_mov = ObjectProperty("")
    _type_mov_dict = {}

    def on_type_mov(self, instance, type_movement):
        """Da usare solo per andare su screen di tipo InsertMovementScreen, in questo modo vengono correttamente attivate
        le schermate a seconda del movimento scelto"""
        if type_movement == "":       # quando torno nella schermata principale setto type_movement = "" in questo caso non mi serve alcun automatismo
            return

        else:
            if not self.has_screen(type_movement):
                self.add_widget(InsertMovementScreen(name=type_movement))

            self.current = type_movement
            self.transition.direction = "left"

            # attivo/disattivo i layout necessari alla compilazione del movimento (parte specifica e parte generale)
            if type_movement in ["Stipendio", "Saldo Debito - Credito"]:  # in caso di stipendio o saldo d/c  non mi serve la schermata principale, quindi nascono label e layout
                self.current_screen.ids.layout_main.opacity = 0
                self.current_screen.ids.layout_main.size_hint_x = 0
                self.current_screen.ids.label_main.opacity = 0
                self.current_screen.ids.label_main.size_hint_x = 0
            else:       # in caso contrario rendo visibile anche il layout del movimento principale
                self.current_screen.ids.layout_main.visible = True

            id_layout = "layout_" + str(Tools.get_key_from_dict(self._type_mov_dict, type_movement))     # id del layout del movimento scelto da attivare
            self.current_screen.ids[id_layout].opacity = 1
            self.current_screen.ids[id_layout].size_hint_x = 0.35
            self.current_screen.ids[id_layout].visible = True   # rendo visibile il layout del movimento specifico

    def go_to_main_screen(self, direction="right"):
        """Essendo che le istruzioni per cambiare schermo sono più di una, le raccolgo tutte nello stesso metodo"""
        self.current = "main"
        self.transition.direction = direction
        self.type_mov = ""


class LoginScreen(Screen):
    """Schermata di login, se le credenziali inserite sono corrette si può accedere alla schermata principale"""
    pass


class MainScreen(Screen):
    """Schermata principale in cui scelgo quale azione compiere: inserire un movimento generico o deb/cred, visualizzare
    i movimenti già inseriti oppure aprire la BI"""

    def show_movements(self):
        """Attiva il layout per visualizzare i tipi di moviemento generici"""
        movements_list = App.get_running_app().wallet_instance.get_movements(type_mov="general").values()
        self.ids.general_mov.update_layout(movements_list)
        self.ids.general_mov.opacity = 1
        self.ids.general_mov.size_hint_x = 0.4
        self.ids.deb_cred.opacity = 0
        self.ids.deb_cred.size_hint_x = 0

    def show_deb_cred(self):
        """Attiva il layout per visualizzare i tipi di movimento deb/cred"""
        self.ids.deb_cred.opacity = 1
        self.ids.deb_cred.size_hint_x = 0.35
        self.ids.general_mov.opacity = 0
        self.ids.general_mov.size_hint_x = 0

    def show_last_movements(self):
        """Va allo screen ShowMovementsScreen"""
        self.manager.current = "show_movements"
        self.manager.transition.direction = "up"

    def open_bi(self):
        """Apre la BI (file qlik)"""
        App.get_running_app().open_BI()

    def set_movement(self, instance_btn):
        """Una volta scelto il movimento specifico cambia schermo su InsertMovementScreen"""
        self.manager.type_mov = instance_btn.text


class InsertMovementScreen(Screen):
    """Schermata d'inserimento dei dati del movimento, contiene già tutti i layout di ogni movimento i quali vengono
    attivati a seconda del tipo di mov. passato"""

    def on_enter(self):
        """Aggiorna tutti i layout dinamici presenti nello screen, popolandoli con le informazioni presenti nel db"""
        for dynamic_layout in self.ids.values():        # aggiorna tutti i layout dinamici
            if isinstance(dynamic_layout, LayoutMov) and dynamic_layout.visible is True:
                dynamic_layout.refresh_dynamic_objs()

    def on_leave(self):
        """Svuota le informazioni parzialmente inserite nello screen"""
        App.get_running_app().main_mov_dict.clear()         # svuoto i dizionari
        App.get_running_app().spec_mov_dict.clear()
        App.get_running_app().date_dict.clear()

        for dynamic_layout in self.ids.values():            # svuoto i layout dinamici
            if isinstance(dynamic_layout, LayoutMov) and dynamic_layout.visible is True:
                dynamic_layout.clear_dynamic_objs()

        list_sub_obj = self.children
        for widget in list_sub_obj:                         # svuoto i textinput
            if widget.children:                             # se il widget ha figli li aggiungo a quelli da verificare che siano TextInput
                list_sub_obj.extend(widget.children)
            if isinstance(widget, TextInput):               # svuoto i TextInput
                widget.text = ""

    def interrupt_insertion(self):
        """Nel caso si voglia chiudere una schermata d'inserimento movimento con i campi parzialmente compilati: se
        ho inserito almeno un valore nei campi allora apro il popup di conferma per l'uscita, se no chiudo
        direttamente"""

        if App.get_running_app().main_mov_dict != {} or App.get_running_app().spec_mov_dict != {}:
            Factory.DoubleChoicePopup(info="Esci senza inserire il movimento?", func_to_exec=self.manager.go_to_main_screen).open()

        else:   # non ho inserito nessun dato, vado direttamente alla schermata iniziale
            self.manager.go_to_main_screen()


class PayOffScreen(Screen):
    """Schermata per gestire la selezione di uno o più debiti/crediti, essi possono essere eliminati o saldati
    chiamando lo screen InsertMovementScreen; nb: è possibile fare saldi (o rimozioni) multipli, il segno finale
    della somma determinerà se si tratta di una spesa o di un'entrata"""
    selected_ids = []  # lista degli id dei record selezionati da eliminare o da saldare

    def on_enter(self):
        """Ogni volta che entro nello screen aggiorno la tabella visualizzata"""
        self.update_rows()

    def on_leave(self, *args):
        """Ogni volta che abbandono lo screen svuoto la tabella e nascondo il bottone di saldo debito/credito"""
        self.selected_ids.clear()                       # cancello gli id dei record selezionati
        self.ids.deb_cred_columns.clear_widgets()       # svuoto i nomi dei campi letti
        self.ids.deb_cred_tab.clear_widgets()           # svuoto la tabella
        self.hide_box(self.ids.appearing_box)           # faccio sparire il box di eliminazione/saldo

    def update_rows(self):
        """Aggiorna i record della tabella e i nomi dei campi leggendoli dal db"""
        try:
            self.selected_ids.clear()                       # cancello gli id dei record selezionati
            cols, rows = App.get_running_app().wallet_instance.get_open_deb_creds()

        except Wallet.FatalError as error:
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
            self.hide_box(self.ids.appearing_box)
        else:                                       # in caso contrario lo faccio apparire
            self.show_box(self.ids.appearing_box)

    def show_box(self, widget_instance, size_hint_x=0.45):
        """Rende visibile un widget"""
        widget_instance.opacity = 1
        widget_instance.size_hint_x = size_hint_x

    def hide_box(self, widget_instance):
        """Nasconde un widget"""
        widget_instance.opacity = 0
        widget_instance.size_hint_x = 0

    def go_to_insert_screen(self):
        """Selezionati uno o più debiti/crediti da saldare vado in InsertMovementScreen per inserire le informazioni
        rimanenti"""
        # verifico che i debiti/crediti selezionati siano relativi alla stessa persona
        if App.get_running_app().wallet_instance.check_ids_to_pay(list(self.selected_ids)) is True:
            App.get_running_app().spec_mov_dict["ID_PREV_DEB_CRED"] = list(self.selected_ids)
            self.manager.type_mov = "Saldo Debito - Credito"    # vado allo screen InsertMovementScreen
        else:
            Factory.ErrorPopup(err_text="Sono stati selezionati debiti e crediti da diversa origine").open()

    def remove_records(self):
        """Rimuove i record (cioè i movimenti), aggiorna la tabella e nasconde il box per la rimozione dei record
        selezionati"""
        App.get_running_app().drop_records(self.selected_ids, "Debito - Credito")
        self.update_rows()
        self.hide_box(self.ids.appearing_box)


class ShowMovementsScreen(Screen):
    """Mostra gli ultimi movimenti inseriti appartenenti ad una tipologia specifica"""
    records_to_drop = []  # lista contenente gli id dei record da eliminare
    try:
        _max_rows_to_show = Config.getint("wallet_app", "max_rows_to_show")             # numero righe massimo da mostrare
        _default_rows_to_show = Config.getint("wallet_app", "default_rows_to_show")     # numero righe impostato all'inizio
    except ValueError:  # in caso di valori non corretti inseriti nel file .ini uso il default
        _max_rows_to_show = 50
        _default_rows_to_show = 10

    def __init__(self, **kw):
        self.type_movement = ""                                 # tipo di movimento scelto da esporre
        self.records_to_show = self._default_rows_to_show       # numero di record da mostrare
        # se entrambi i seguenti flag sono True posso visualizzare la tabella
        self._selected_records_to_show = True                   # flag t/f se ho impostato quante righe visualizzare (di default è sempre valorizzato)
        self._selected_movement = False                         # flag t/f se ho selezionato il movimento
        super().__init__(**kw)

    def on_enter(self):
        """Quando entro nello screen aggiorno il layout contenete i tipi di movimenti (entrata, spesa generica, ...) da
        visionare"""
        self.ids.info_no_rows.text = self.ids.info_no_rows.text.format(self.records_to_show)                    # attivo la scritta
        list_movements = App.get_running_app().wallet_instance.get_movements(type_mov="general").values()       # lista dei possibili movimenti da selezionare
        self.ids.box_movements.update_layout(list_movements)                                                    # aggiorno il relativo layout

    def on_leave(self):
        """Rimuovo tutte le informazioni precedentemente inserite"""
        self.type_movement = ""                     # movimento scelto
        self.records_to_drop.clear()                # svuoto la lista di eventuali record selezionati
        self.ids.mov_columns.clear_widgets()        # svuoto il contenitore dei nomi dei campi
        self.ids.rows_box.clear_widgets()           # svuoto la tabella
        self.ids.box_movements.clear_widgets()      # svuoto il contenitore dei movimenti
        self.hide_box(self.ids.remove_record_btn)   # faccio sparire il bottone per rimuovere i record

    def set_new_number(self, new_number):
        """Aggiorno il nuovo numero di record da mostrare inserito in input, aggiorno anche la GUI"""
        if new_number.isdigit():
            self.records_to_show = int(new_number)

            if self.records_to_show > self._max_rows_to_show:   # non deve essere superiore ad un max per evitare troppi rallentamenti
                self.records_to_show = self._max_rows_to_show

            self.ids.info_no_rows.text = "Record da visualizzare: [color=f0f3f4]{}[/color]".format(self.records_to_show)
            self._selected_records_to_show = True

            if self._selected_movement is True:     # la tabella è già attiva, la aggiorno
                self.update_rows()

        else:
            self.ids.info_no_rows.text = "Record da visualizzare: [color=cb4335][i]non valido[/i][/color]"
            self._selected_records_to_show = False

    def set_movement(self, btn_instance):
        """Una volta selezionato il movimento scelto, e se è inserito un valore valido per il numero dei record da
        recuperare, mostra la tabella"""
        self.type_movement = btn_instance.text
        self._selected_movement = True

        if self._selected_records_to_show is True:
            self.update_rows()

    def update_rows(self):
        """Leggo dal db le n righe dalla tabella del movimento selezionato, aggiorno due widget: il contenitore dei
        nomi dei campi e uno che contiene i record della tabella del db"""
        self.records_to_drop.clear()                # svuoto eventuali id selezionati in precedenza
        field_name_box = self.ids.mov_columns       # box contenente i nomi dei campi
        rows_box = self.ids.rows_box                # tabella contenente i vari record

        try:
            col_names, rows = App.get_running_app().wallet_instance.get_last_n_records(self.records_to_show, self.type_movement)

        except (Wallet.WrongValueInsert, Wallet.FatalError) as error:
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
            self.hide_box(self.ids.remove_record_btn)
        else:
            self.show_box(self.ids.remove_record_btn)

    def show_box(self, widget_instance, size_hint_x=0.2):
        """Rende visibile un widget"""
        widget_instance.opacity = 1
        widget_instance.size_hint_x = size_hint_x

    def hide_box(self, widget_instance):
        """Nasconde un widget"""
        widget_instance.opacity = 0
        widget_instance.size_hint_x = 0

    def remove_records(self):
        """Rimuove il/i record, e aggiorno la tabella"""
        App.get_running_app().drop_records(self.records_to_drop, self.type_movement)
        self.update_rows()
        self.hide_box(self.ids.remove_record_btn)


# oggetti di servizio
class BKG(Widget):
    """Oggetto canvas che permette di colorare sfondo e bordi del widget"""
    bkg_color = ObjectProperty(None)
    border_color = ObjectProperty(None)


class BKGlabel(BKG):
    """Colore delle caselle testuali"""
    pass


class BKGbutton(BKG):
    """Colore dei bottoni"""
    pass


class BKGrowLayout(BKG):
    """Cornice di contenimento dei layout di selezione delle righe"""
    pass


class BKGselectionButton(BKG):
    """Colore dei bottoni a selezione"""
    pass


class DefaultLabel(Label, BKGlabel):
    """Normale label utilizzata"""
    pass


class DefaultButton(Button, BKGbutton):
    """Bottone standard (parent_layout rappresenta l'eventuale widget che lo contiene); quando viene premuto ci sono due
    modifiche:
        1) a livello GUI per rappresentare visivamente la pressione del bottone
        2) e se parent_layout != None segnala la pressione al container nel caso debba essere eseguita un'azione a
        a seguito della pressione"""
    parent_layout = ObjectProperty(None)

    def on_state(self, instance, pressed):
        """Alla pressione modifico GUI ed eventualmente eseguo il callback a self.parent_layout"""
        if pressed == "down":
            if self.parent_layout:
                self.parent_layout.btn_pressed(self)
            self.bkg_color.pop()
            self.bkg_color.append("0.75")
            self.background_color = self.bkg_color

        else:
            self.bkg_color.pop()
            self.bkg_color.append("1")
            self.background_color = self.bkg_color


class SelectionButton(Button, BKGselectionButton):
    """Bottone che rimane attivo una volta premuto, self.activate segnala se esso è attivo o meno, vedi DefaultButton
    per self.parent_layout"""
    activate = ObjectProperty(False)                      # True/False se è premuto o meno
    parent_layout = ObjectProperty(None)

    def on_activate(self, instance, activate):
        """Ad ogni pressione attivo il bottone se era disattivato o viceversa"""
        if activate is False:  # se viene rilasciato il bottone metto in bianco il colore del font e quello background com'era prima
            self.color = [1, 1, 1, 1]
            self.background_color = self.bkg_color
        else:  # se viene premuto il bottone metto il colore del font come quello del background, quello dello sfondo diventa verde
            self.color = App.get_running_app().get_color("darkgrey_rgba")
            self.background_color = [0, 1, 0, 1]

    def on_press(self):
        """Eseguo l'evenetuale callback a self.parent_layout e modifico il parametro self.activate"""
        if self.parent_layout:
            self.parent_layout.btn_pressed(self)
        self.activate = not self.activate


class DefaultTextInput(TextInput):
    """TextInput standard, definito in MyDefaultWidgets.kv"""
    pass


class DefaultBoxLayout(BoxLayout):
    """Lo dichiaro per settare alcuni valori (padding, spacing e orientation) in MyDefaultWidgets.kv"""
    pass


class DefaultScrollView(ScrollView):
    """Lo dichiaro per settare alcuni valori fissi in MyDefaultWidgets.kv"""
    pass


class InputLayout(DefaultBoxLayout):
    """Questo Layout contiene il comportamento per eseguire una determinata azione se uno dei sui widget figli viene
    premuto"""
    def __init__(self, type_selection="multiple", f_to_launch=None, **kw):
        self.type_selection = type_selection        # tipi di selezione dei bottoni: 'single', 'multiple' o 'all' (vedi self.btn_pressed())
        self.f_to_launch = f_to_launch              # funzione da eseguire alla pressione
        super().__init__(**kw)

    def btn_pressed(self, btn_instance):
        """self.btn_pressed() viene chiamata sia da DefaultButton sia da SelectionButton nei metodi on_state() o on_press()
        rispettivamente, lancia la funzione, se essa è definita, e modifica l'attivazione dei bottoni a seconda del
        parametro self.type_selection"""
        if self.f_to_launch:
            self.f_to_launch(btn_instance)
        if self.type_selection == "single":     # 'single' = soltanto un bottone puà rimanere attivo nello stesso momento
            for btn in [selection_btn for selection_btn in self.children if isinstance(selection_btn, SelectionButton)]:
                if btn != btn_instance and btn.activate is True:
                    btn.activate = False        # quindi disattivo ogni altro bottone precedentemente attivo
        elif self.type_selection == "all":      # 'all' = alla pressione attivo tutti i bottoni contenuti nel widget (vedi RowInputLayout)
            for btn in [selection_btn for selection_btn in self.children if isinstance(selection_btn, SelectionButton)]:
                if btn != btn_instance:
                    btn.activate = not btn_instance.activate  # il not è perchè btn_instance.activate è già stato modificato, quindi mi serve il valore opposto


class DynamicLayout(DefaultBoxLayout):
    """Questo Layout contiene il comportamento per venire riempito in automatico con il metodo self.update_layout() una
    una volta che gli viene passata una lista in argomento. Parametri da valorizzare del file .kv:
        - font_size_chars: dimensione del font di ogni widget figlio;
        - color_widgets: colore di ogni widget figlio"""
    def update_layout(self, field_list):
        pass


class LabelDynamicLayout(DynamicLayout):
    """Layout dinamico, crea una serie di label per ogni elemento della lista passata"""
    def update_layout(self, field_list):
        self.clear_widgets()
        for label_name in field_list:
            label = DefaultLabel(text=label_name,
                                 font_size=self.font_size_chars * 0.6,
                                 bkg_color=self.color_widgets,
                                 border_color=[1, 1, 1, 1],
                                 color=[1, 1, 1, 1])
            self.add_widget(label)


class ButtonDynamicInputLayout(DynamicLayout, InputLayout):
    """Layout popolato dinamicamente con dei bottoni e che gestisce l'input se viene premuto un bottone"""
    _type_btns = {"default": DefaultButton, "selection": SelectionButton}  # dict dei tipi possibili di btn da inserire nel box

    def __init__(self, type_btn="selection", **kw):
        super().__init__(**kw)
        self.type_btn = type_btn            # tipo di bottone: "selection" --> MySelectionButton, "default" --> DefaultButton
        self.type_selection = "single"      # metto single di default: non può esserci più di un bottone attivo in contemporanea

    def update_layout(self, field_list):
        """Creo un bottone per ogni elemento della lista field_list, la classe (DefaultButton o SelectionButton) dipende
        dal parametro self.type_btn"""
        self.clear_widgets()
        Btn_class = self._type_btns[self.type_btn]
        for field in field_list:
            btn = Btn_class(bkg_color=self.color_widgets,
                            text=field,
                            font_size=self.font_size_chars)
            btn.parent_layout = self
            self.add_widget(btn)


class RowDynamicInputLayout(DynamicLayout, InputLayout):
    """Layout popolato dinamicamente con dei bottoni che si attivano/disattivano tutti alla pressione di uno di questi;
    questo tipo di widget è pensato per popolare TableDynamicInputLayout, la quale rappresenta una tabella contenete vari
    record/righe e gestisce inoltre l'input se viene premuto un bottone"""
    def __init__(self, id_record, **kw):
        super().__init__(**kw)
        self.id_record = id_record      # id del record
        self.type_selection = "all"     # all di default: alla pressione attivo/disattivo tutti i bottoni della riga

    def update_layout(self, field_list):
        """Creo un bottone di tipo SelectionButton per ogni elemento della lista field_list"""
        self.clear_widgets()
        for btn_name in field_list:
            label_field = SelectionButton(text=str(btn_name),
                                          font_size=self.font_size_chars * 0.45,
                                          bkg_color=self.color_widgets,
                                          parent_layout=self)

            self.add_widget(label_field)


class TableDynamicInputLayout(DynamicLayout, InputLayout):
    """Istanza di DynamicLayout pensata per contenere una tabella, ogni riga-record è un'istanza di RowDynamicInputLayout la quale
    contiene un bottone per ogni campo, gestisce inoltre l'input se viene premuto un bottone (una riga i questo caso);
    parametri da valorizzare nel file .kv:
        - size_records: altezza (in pixel) di ogni riga che compone la tabella"""
    def update_layout(self, field_list):
        """Aggiorna la tabella con la lista field_list, crea n righe di RowDynamicInputLayout ciascuna composta da m bottoni,
         questi vengono inseriti con il metodo RowDynamicInputLayout.update_row(list)"""
        self.clear_widgets()
        self.height = len(field_list) * self.size_records
        for record in field_list:
            id_record = record[-1]
            record.pop()
            row = RowDynamicInputLayout(id_record=id_record,
                                        f_to_launch=self.f_to_launch,
                                        height=self.size_records)

            row.update_layout(record)
            self.add_widget(row)

    def btn_pressed(self, btn_instance):
        """è necessario fare questo passaggio intermedio: pressione bottone --> attivazione/disattivazione della riga
        che lo contiene"""
        btn_instance.parent_layout.btn_pressed(btn_instance)


# layout per l'inserimento dei dati dei movimenti
class LayoutMov(DefaultBoxLayout, BKGrowLayout):
    """Istanza di DefaultBoxLayout, contiene inoltre un background che lo incornicia"""
    def __init__(self, **kw):
        self.visible = False
        super().__init__(**kw)

    def refresh_dynamic_objs(self):
        """Se contiene alcuni widget dinamici, i.e. estendono la classe DyamicLayout, aggiorna tutti quelli che sono ivi
        contenuti"""
        pass

    def clear_dynamic_objs(self):
        """Se contiene alcuni widget dinamici, i.e. estendono la classe DyamicLayout, svuota tutti quelli che sono ivi
        contenuti"""
        pass


class LayoutMainMov(LayoutMov):
    """Layout di inserimento delle informazioni generiche del movimento, il parametro _payments_dict è un dizionario che
    contiene tutti i possibili tipi di pagamento selezionabili nella forma id_pagamento: nome_pagamento, popolato
    in self.refresh_dynamic_objs()"""
    _payments_dict = {}  # dizionario dei tipi di pagamenti presenti nel db

    def set_payment(self, btn_instance):
        """Aggiungo/rimuovo il pagmento selzionato a main_mov_dict"""
        id_pag = Tools.get_key_from_dict(self._payments_dict, btn_instance.text)
        if "ID_PAG" in App.get_running_app().main_mov_dict.keys() and id_pag == App.get_running_app().main_mov_dict["ID_PAG"]:
            App.get_running_app().main_mov_dict.pop("ID_PAG")
        else:
            App.get_running_app().main_mov_dict["ID_PAG"] = id_pag

    def refresh_dynamic_objs(self):
        """Vedi LayoutMov.refresh_dynamic_objs()"""
        self._payments_dict = App.get_running_app().wallet_instance.get_type_payments()  # popolo il dizionario dei tipi di pagamenti presenti nel db
        self.ids.input_payments.update_layout(self._payments_dict.values())              # aggiorno i widget dinamici

    def empty_dynamic_objs(self):
        """Vedi LayoutMov.empty_dynamic_objs()"""
        self.ids.input_payments.clear_widgets()


class LayoutData(LayoutMov):
    """Schermata che permette di inserire una data nel formato giorno-mese-anno, salvati in 3 variabili indipendenti"""
    pass


class LayoutSpesaGenerica(LayoutMov):
    """Layout di inserimento delle informazioni del movimento di tipo spesa generica; _type_spec_movements_dict è un
    dizionario che contiene tutti i possibili tipi di tipi specifici di spesa selezionabili, nella forma
    id_spesa: nome_spesa, popolato in self.refresh_dynamic_objs()"""
    _type_spec_movements_dict = {}  # dizionario dei tipi di spese variabili presenti nel db

    def set_spec_movement(self, btn_instance):
        """Aggiungo/rimuovo il tipo di spesa selezionata a spec_mov_dict"""
        id_spesa = Tools.get_key_from_dict(self._type_spec_movements_dict, btn_instance.text)
        if "ID_TIPO_SPESA" in App.get_running_app().spec_mov_dict.keys() and id_spesa == App.get_running_app().spec_mov_dict["ID_TIPO_SPESA"]:
            App.get_running_app().spec_mov_dict.pop("ID_TIPO_SPESA")
        else:
            App.get_running_app().spec_mov_dict["ID_TIPO_SPESA"] = id_spesa

    def refresh_dynamic_objs(self):
        """Vedi LayoutMov.refresh_dynamic_objs()"""
        self._type_spec_movements_dict = App.get_running_app().wallet_instance.get_type_spec_movements()    # dizionario dei tipi di spese variabili presenti nel db
        self.ids.input_tipo_spesa.update_layout(self._type_spec_movements_dict.values())                    # aggiorno i widget dinamici

    def empty_dynamic_objs(self):
        """Vedi LayoutMov.empty_dynamic_objs()"""
        self.ids.input_tipo_spesa.clear_widgets()


class LayoutSpesaFissa(LayoutMov):
    """Layout di inserimento delle informazioni del movimento di tipo spesa fissa (descrizione)"""
    pass


class LayoutStipendio(LayoutMov):
    """Layout di inserimento delle informazioni del movimento di tipo stipendio"""
    pass


class LayoutEntrata(LayoutMov):
    """Layout di inserimento delle informazioni del movimento di tipo entrata"""
    _type_entrate_dict = {}  # dizionario dei tipi di entrate presenti nel db

    def set_tipo_entrata(self, btn_instance):
        """Aggiungo/rimuovo il tipo di entrata selezionata a spec_mov_dict"""
        id_ent = Tools.get_key_from_dict(self._type_entrate_dict, btn_instance.text)
        if "ID_TIPO_ENTRATA" in App.get_running_app().spec_mov_dict.keys() and id_ent == App.get_running_app().spec_mov_dict["ID_TIPO_ENTRATA"]:
            App.get_running_app().spec_mov_dict.pop("ID_TIPO_ENTRATA")
        else:
            App.get_running_app().spec_mov_dict["ID_TIPO_ENTRATA"] = id_ent

    def refresh_dynamic_objs(self):
        """Vedi LayoutMov.refresh_dynamic_objs()"""
        self._type_entrate_dict = App.get_running_app().wallet_instance.get_type_entrate()  # aggiorno il dizionario
        self.ids.input_tipo_entrata.update_layout(self._type_entrate_dict.values())  # aggiorno i widget dinamici

    def empty_dynamic_objs(self):
        """Vedi LayoutMov.empty_dynamic_objs()"""
        self.ids.input_tipo_entrata.clear_widgets()


class LayoutDebitoCredito(LayoutMov):
    """Layout di inserimento delle informazioni  del movimento di tipo debito/credito"""
    _deb_cred_list = ["DEBITO", "CREDITO"]

    def set_deb_cred(self, btn_instance):
        """Aggiorno spec_mov_dict con il tipo scelto: debito o credito"""
        deb_cred = btn_instance.text
        if deb_cred in self._deb_cred_list:
            App.get_running_app().spec_mov_dict["DEBCRED"] = "1" if deb_cred == "CREDITO" else "0"

    def refresh_dynamic_objs(self):
        """Vedi LayoutMov.refresh_dynamic_objs()"""
        self.ids.input_deb_cred.update_layout(self._deb_cred_list)   # aggiorno i widget dinamici

    def empty_dynamic_objs(self):
        """Vedi LayoutMov.empty_dynamic_objs()"""
        self.ids.input_deb_cred.clear_widgets()


class LayoutSaldoDebitoCredito(LayoutMov):
    """Layout di inserimento delle informazioni per saldare uno o più debiti/crediti esistenti; il parametro
    _payments_dict è un dizionario che contiene tutti i possibili tipi di pagamento selezionabili nella forma
    id_pagamento: nome_pagamento, popolato in self.refresh_dynamic_objs()"""
    _payments_dict = {}  # dizionario dei tipi di pagamenti presenti nel db

    def set_payment(self, btn_instance):
        """Aggiungo/rimuovo il pagmento selzionato a main_mov_dict"""
        id_pag = Tools.get_key_from_dict(self._payments_dict, btn_instance.text)
        if "ID_PAG" in App.get_running_app().main_mov_dict.keys() and id_pag == App.get_running_app().main_mov_dict["ID_PAG"]:
            App.get_running_app().main_mov_dict.pop("ID_PAG")
        else:
            App.get_running_app().main_mov_dict["ID_PAG"] = id_pag

    def refresh_dynamic_objs(self):
        """Vedi LayoutMov.refresh_dynamic_objs()"""
        self._payments_dict = App.get_running_app().wallet_instance.get_type_payments()     # dizionario dei tipi di pagamenti presenti nel db
        self.ids.input_payments.update_layout(self._payments_dict.values())                 # aggiorno i widget dinamici

    def empty_dynamic_objs(self):
        """Vedi LayoutMov.empty_dynamic_objs()"""
        self.ids.input_payments.clear_widgets()


class LayoutSpesaMantenimento(LayoutMov):
    """Layout di inserimento delle informazioni del movimento di tipo spesa di mantenimento"""
    pass


class LayoutSpesaViaggio(LayoutMov):
    """Layout di inserimento delle informazioni del movimento di tipo spesa di viaggio"""
    pass


# Popup
class ErrorPopup(Popup):
    """Popop che compare al verificarsi di errori, il parametro err_text contiene informazioni sull'anomalia
    verificatasi"""
    err_text = ObjectProperty("")


class InfoPopup(ModalView):  # ModalView e non Popup perchè in questo caso non uso non mi serve il titolo
    """Popup che permette, generalmente, di avvisare del successo di un'azione di inserimento movimento, parametri:
        - info -> avviso del layout (va nel titolo)
        - func_to_exec -> se <> None viene eseguita quando si preme il bottone con scritto OK"""
    info = ObjectProperty("")
    func_to_exec = ObjectProperty(None)

    def exec_function(self):
        self.dismiss()
        if self.func_to_exec:
            self.func_to_exec()


class SingleChoicePopup(InfoPopup):
    """Questo popup ha un solo bottone da premere, oltre alla descrizione informativa"""
    pass


class DoubleChoicePopup(InfoPopup):
    """Questo popup ha una scelta del tipo 'annulla'/'procedi', oltre alla descrizione informativa
        - second_func_to_exec -> se <> None viene eseguita quando si preme il bottone con scritto ANNULLA"""
    second_func_to_exec = ObjectProperty(None)

    def exec_second_function(self):
        self.dismiss()
        if self.second_func_to_exec:
            self.second_func_to_exec()


class WalletApp(App):
    """Applicazione principale che gestisce il front end con l'utente, essa permette:
        1) la modifica delle informazioni, inserendo nuovi movimenti o saldando debiti/crediti esistenti
        2) l'accesso alla BI per analisi"""

    def __init__(self, **kwargs):
        # recupero alcune informazioni dal file wallet_config.ini e creo il log con il metodo create_logger()
        self._colors = {key: value for key, value in Config["kivy_colors"].items()}
        log_level = Config.getint("log", "level")
        path_log_file = Config["log"]["path_log_file"]
        name_log_file = Config["log"]["name_log_file"]
        format_lines_log = Config["log"]["format_log_file"]
        Tools.create_logger(logger_name="wallet_logger", log_level=log_levels[log_level], log_path=path_log_file, log_name=name_log_file, fmt=format_lines_log)

        self.title = 'WALL€T'                                       # nome dell'app
        self.wallet_instance = None                                 # istanza di wallet per accedere al database
        self.manager = None                                         # istanza di ScreenManager per muoversi tra le schermate
        self.qlik_app = None                                        # istanza dell'app di QlikView
        self._stopped = False                                       # proprietà di servizio, vedi self.on_stop()
        self.date_dict = {}                                         # data movimento
        self.main_mov_dict = {}                                     # informazioni generali (comuni ad ogni tipo di spesa/entrata)
        self.spec_mov_dict = {}                                     # informazioni specifiche della spesa/entrata
        super().__init__(**kwargs)

        logging.info("[%-10s]: %s", "WalletApp", "#" * 80)
        logging.info("[%-10s]: avvio app - applicazione avviata" % "WalletApp")

    def build(self):
        """Carico i file .kv e creo il primo screen per il login"""
        try:
            for kv_file in Config["kivy_files"].values():
                Builder.load_file(kv_file)

        except FileNotFoundError:
            raise AppException("Errore GUI - fogli di stile (.kv) non trovati")

        else:
            self.manager = ManagerScreen()
            self.manager.add_widget(LoginScreen(name="login"))  # gli altri Screen verranno lanciati direttamente da self.manager
            logging.info("[%-10s]: avvio app - caricati i file di stile .kv, creato ScreenManager e Screen di login" % "WalletApp")
            return self.manager

    def connect(self):
        """Effettua la connessione al database tramite l'istanza di wallet e il dsn passato, creo inoltre l'app per
        accedere al file .qvw, se tutto avviene con successo crea lo screen principale dell'app"""
        try:
            self.wallet_instance = Wallet.Wallet(Config["database"]["dsn_name"])       # DSN di collegamento all'istanza di SQL Server
            self.qlik_app = Wallet.QlikViewApp(Config["bi"]["path_qlik_file"])         # percorso in cui è salvato il file di QlikView della BI

        except Wallet.FatalError as err:
            Factory.ErrorPopup(err_text=str(err)).open()
            return False

        else:
            return True

    def try_login(self, user, pwd, auto_login=False):
        """Una volta fatta la connessione al db si accede all'app di wallet tramite l'inserimento delle credenziali,
        ciò avviene con il metodo Wallet.login_wallet():
         - auto_login -> se vale True il login viene fatto in automatico senza controllo, mi serve per sveltire l'accesso quando sono in test"""
        if self.wallet_instance is None:
            logging.error("[%-10s]: login app - tentativo di accesso al database senza che sia stata creata correttamente la connessione" % "WalletApp")
            Factory.ErrorPopup(err_text="Tentativo di accesso senza connessione al database").open()
        elif auto_login is True:      # skippo l'accesso (NB solo per test)
            pass
        elif user == "" or pwd == "":
            Factory.ErrorPopup(err_text="Credenziali mancanti").open()
        else:
            try:
                login_status = self.wallet_instance.login_wallet(user.strip(), pwd.strip())
            except Wallet.FatalError as db_error:
                Factory.ErrorPopup(err_text=str(db_error)).open()
            else:
                if login_status is True:
                    self.manager._type_mov_dict = self.wallet_instance.get_movements()   # ricavo i tipi di movimenti disponibili
                    self.manager.add_widget(MainScreen(name="main"))                     # creo lo screen principale
                    self.manager.add_widget(PayOffScreen(name="open_deb_cred"))          # quello dei debiti/crediti aperti
                    self.manager.add_widget(ShowMovementsScreen(name="show_movements"))  # e quello per visualizzare i movimenti inseriti
                    self.manager.go_to_main_screen(direction="left")                     # vado alla schermata principale
                else:
                    popup = Factory.SingleChoicePopup()
                    popup.info = "Credenziali non corrette, login fallito"
                    popup.open()

    def open_BI(self):
        """Apro il file QlikVew contenente la BI di Wallet"""
        try:
            user, pwd = self.wallet_instance.get_bi_credentials()
            self.qlik_app.open(user, pwd)

        except Wallet.FatalError as generic_error:
            Factory.ErrorPopup(err_text=str(generic_error)).open()

    def check_movement(self):
        """inscatola il metodo wallet.check_values(), verifica di tutte le informazioni inserite"""
        try:
            self.wallet_instance.check_values(
                type_movement=self.manager.type_mov,
                date_mov=self.date_dict,
                main_mov_dict=self.main_mov_dict,
                spec_mov_dict=self.spec_mov_dict)

        # lancio popup se fallisce il check dei dati inseriti (WrongValueInsert) o per errore generico (FatalError))
        except (Wallet.WrongValueInsert, Wallet.FatalError) as error:
            Factory.ErrorPopup(err_text=str(error)).open()
            return False

        else:
            return True

    def insert_movement(self):
        """Deve essere chiamato dopo il metodo check_movement(); inserisce i valori del database"""
        try:
            self.wallet_instance.insert_movement()

        except (Wallet.WrongValueInsert, Wallet.FatalError, Tools.WrongSQLstatement) as error:
            Factory.ErrorPopup(err_text=str(error)).open()

        else:  # inserimento effettuato
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
        db_name = Config["database"]["database_name"]
        backup_path = Config["database"]["backup_path"]

        try:
            self.wallet_instance.backup_database(db_name, backup_path)

        except Wallet.FatalError as err:
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

    def get_color(self, color_id):
        """Nel dizionario self._colors sono salvati gli rgba dei colori usati nell'app: viene restiuito il valore rgba
        della chiave passata; viene convertito in lista dal metodo get_list_from_str essendo che è salvato sotto forma
        di stringa"""

        return Tools.str_to_list(self._colors[color_id])


if __name__ == "__main__":
    app = WalletApp()
    app.run()
