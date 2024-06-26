from kivy.uix.boxlayout import BoxLayout
from DefaultWidgets import *
from AppExceptions import *


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
        self.type_selection = type_selection        # tipi di selezione dei bottoni: 'single', 'multiple' (?) o 'all' (vedi self.btn_pressed())
        self.f_to_launch = f_to_launch              # funzione da eseguire alla pressione
        self.btn_pressed = None

    def update_state(self, btn_instance):    # NB se premo per due volte sullo stesso bottone viene correttamente gestito?
        """self.btn_pressed() viene chiamata sia da DefaultButton sia da DefaultSelectionButton nei metodi on_state() o on_press()
        rispettivamente, lancia la funzione, se essa è definita, e modifica l'attivazione dei bottoni a seconda del
        parametro self.type_selection"""
        self.btn_pressed = btn_instance
        if self.f_to_launch:
            self.f_to_launch(btn_instance.get_alt_id())
        if self.type_selection == "single":     # 'single' = soltanto un bottone puà rimanere attivo nello stesso momento
            for btn in [selection_btn for selection_btn in self.children if isinstance(selection_btn, SelectionButton)]:
                if btn != btn_instance and btn.activate is True:
                    btn.activate = False        # quindi disattivo ogni altro bottone precedentemente attivo
        elif self.type_selection == "all":      # 'all' = alla pressione attivo tutti i bottoni contenuti nel widget (vedi RowInputLayout)
            for btn in [selection_btn for selection_btn in self.children if isinstance(selection_btn, SelectionButton)]:
                if btn != btn_instance:
                    btn.activate = not btn_instance.activate  # il not è perchè btn_instance.activate è già stato modificato, quindi mi serve il valore opposto

    def id_active_btn(self):
        if self.btn_pressed:
            return self.btn_pressed.get_alt_id()
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
    def update_layout(self, field_map):
        self.clear_widgets()
        self.btn_pressed = None
        for field_id, field_name in field_map.items():
            btn = SelectionButton(text=field_name,
                                  font_size=self.font_size_chars,
                                  alt_id=field_id,
                                  background_color=self.color_widgets,
                                  parent_layout=self)
            self.add_widget(btn)


class RowDynamicInputLayout(DynamicLayout, InputLayout):        # NB put RowDynamicInput inside Table...
    def update_layout(self, row_info):
        """Creo un bottone di tipo DefaultSelectionButton per ogni elemento della lista field_list"""
        self.clear_widgets()
        self.btn_pressed = None
        id_row = row_info[0]
        row = row_info[1]
        for field in row:
            button = SelectionButton(text=str(field),
                                     font_size=self.font_size_chars,
                                     alt_id=id_row,
                                     background_color=self.color_widgets,
                                     parent_layout=self)
            self.add_widget(button)


class TableDynamicInputLayout(DynamicLayout, InputLayout):
    def update_layout(self, records):
        """Aggiorna la tabella con la lista records, crea n righe di RowDynamicInputLayout ciascuna composta da m bottoni"""
        self.clear_widgets()
        self.height = len(records) * self.size_records
        for record in records:
            id_record = record[-1]
            record.pop()
            row = RowDynamicInputLayout(font_size_chars=self.font_size_chars,
                                        f_to_launch=self.f_to_launch,
                                        height=self.size_records,
                                        orientation="horizontal")
            row.update_layout([id_record, record])
            self.add_widget(row)

    def btn_pressed(self, btn_instance):
        """è necessario fare questo passaggio intermedio: pressione bottone --> attivazione/disattivazione della riga
        che lo contiene"""
        btn_instance.parent_layout.btn_pressed(btn_instance)