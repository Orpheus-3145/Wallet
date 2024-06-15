from kivy.uix.boxlayout import BoxLayout
from DefaultWidgets import *


class Showable(Widget):
    def __init__(self, **kw):
        self.tmp_size_hint_x = 0
        super().__init__(**kw)

    def on_kv_post(self, base_widget):
        self.tmp_size_hint_x = self.size_hint[0]

    def show_widget(self):
        self.disabled = False
        self.opacity = 1
        self.size_hint[0] = self.tmp_size_hint_x

    def hide_widget(self):
        self.disabled = True
        self.opacity = 0
        self.size_hint[0] = 0


class DefaultLayout(BoxLayout, Showable):
    """Lo dichiaro per settare alcuni valori (padding, spacing e orientation) in DefaultLayouts.kv"""
    pass


class BorderLayout(DefaultLayout, BKGrowLayout):
    pass


class InputLayout(DefaultLayout):
    """Questo Layout contiene il comportamento per eseguire una determinata azione se uno dei sui widget figli viene
    premuto"""
    def __init__(self, type_selection="multiple", f_to_launch=None, **kw):
        super().__init__(**kw)
        self.type_selection = type_selection        # tipi di selezione dei bottoni: 'single', 'multiple' o 'all' (vedi self.btn_pressed())
        self.f_to_launch = f_to_launch              # funzione da eseguire alla pressione
        self.btn_pressed = None

    def update_state(self, btn_instance):    # NB se premo per due volte sullo stesso bottone viene correttamente gestito?
        """self.btn_pressed() viene chiamata sia da DefaultButton sia da DefaultSelectionButton nei metodi on_state() o on_press()
        rispettivamente, lancia la funzione, se essa è definita, e modifica l'attivazione dei bottoni a seconda del
        parametro self.type_selection"""
        self.btn_pressed = btn_instance
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

    def get_selected_value(self):
        if self.btn_pressed:
            return self.btn_pressed.text
        else:
            return ""


class DynamicLayout(DefaultLayout):
    """Questo Layout contiene il comportamento per venire riempito in automatico con il metodo self.update_layout() una
    una volta che gli viene passata una lista in argomento. Parametri da valorizzare del file .kv:
        - font_size_scale: proporzione del font di ogni widget figlio;
        - color_widgets: colore di ogni widget figlio"""
    def __init__(self, font_size_chars=1, **kw):
        super().__init__(**kw)
        self.font_size_chars = font_size_chars

    def update_layout(self, field_list):
        pass


class LabelDynamicLayout(DynamicLayout):
    """Layout dinamico, crea una serie di label per ogni elemento della lista passata"""
    def update_layout(self, field_list):
        self.clear_widgets()
        for label_name in field_list:
            label = DefaultLabel(text=label_name,
                                 font_size=self.font_size_chars,
                                 background_color=self.color_widgets,
                                 border_color=[1, 1, 1, 1],
                                 color=[1, 1, 1, 1])
            self.add_widget(label)


class ButtonDynamicInputLayout(DynamicLayout, InputLayout):
    """Layout popolato dinamicamente con dei bottoni e che gestisce l'input se viene premuto un bottone"""
    _type_btns = {"simple": SimpleButton, "selection": SelectionButton}  # dict dei tipi possibili di btn da inserire nel box

    def __init__(self, type_btn="selection", **kw):
        super().__init__(**kw)
        self.type_btn = type_btn            # tipo di bottone: "selection" --> MySelectionButton, "simple" --> DefaultButton
        self.type_selection = "single"      # metto single di default: non può esserci più di un bottone attivo in contemporanea

    def update_layout(self, field_list):
        """Creo un bottone per ogni elemento della lista field_list, la classe (DefaultButton o DefaultSelectionButton) dipende
        dal parametro self.type_btn"""
        self.clear_widgets()
        btn_class = self._type_btns[self.type_btn]
        for field in field_list:
            btn = btn_class(text=field,
                            font_size=self.font_size_chars,
                            background_color=self.color_widgets,
                            parent_layout=self)
            self.add_widget(btn)


class RowDynamicInputLayout(DynamicLayout, InputLayout):        # NB put RowDynamicInout... inside Table
    def __init__(self, id_record, **kw):
        super().__init__(**kw)
        self.id_record = id_record      # id del record
        self.type_selection = "all"     # all di default: alla pressione attivo/disattivo tutti i bottoni della riga

    def update_layout(self, field_list):
        """Creo un bottone di tipo DefaultSelectionButton per ogni elemento della lista field_list"""
        self.clear_widgets()
        for btn_name in field_list:
            label_field = SelectionButton(text=str(btn_name),
                                          font_size=self.font_size_chars,
                                          background_color=self.color_widgets,
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
            row = RowDynamicInputLayout(font_size_chars=self.font_size_chars,
                                        id_record=id_record,
                                        f_to_launch=self.f_to_launch,
                                        height=self.size_records,
                                        orientation="horizontal",
                                        spacing=2,
                                        padding=0)
            row.update_layout(record)
            self.add_widget(row)

    def btn_pressed(self, btn_instance):
        """è necessario fare questo passaggio intermedio: pressione bottone --> attivazione/disattivazione della riga
        che lo contiene"""
        btn_instance.parent_layout.btn_pressed(btn_instance)

    def get_selected_value(self):
        pass
