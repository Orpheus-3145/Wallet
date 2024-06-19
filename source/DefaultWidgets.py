from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.properties import ListProperty
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView


class BKG(Widget):
    border_color = ListProperty([1, 1, 1, 1])


class Writable(Widget):
    def __init__(self, font_size_scale=1, **kw):
        super().__init__(**kw)
        self.font_size_scale = font_size_scale

    def on_kv_post(self, base_widget):
        self.font_size *= self.font_size_scale


class BKGlabel(BKG):
    background_color = ListProperty([1, 1, 1, 1])


class BKGrowLayout(BKG):
    pass


class DefaultLabel(Label, BKGlabel, Writable):
    pass


class DefaultButton(Button, Writable):
    def __init__(self, parent_layout=None, alt_id=None, **kw):
        super().__init__(**kw)
        self.parent_layout = parent_layout
        self.alt_id = alt_id

    def get_alt_id(self):
        return self.alt_id

    def on_state(self, instance, pressed):
        if pressed == "down":
            self.background_color.pop()
            self.background_color.append(0.75)
            if self.parent_layout:
                self.parent_layout.update_state(self)
        else:
            self.background_color.pop()
            self.background_color.append(1)


class SelectionButton(DefaultButton):
    """Bottone che rimane attivo una volta premuto, self.activate segnala se esso è attivo o meno, vedi DefaultButton
    per self.parent_layout"""
    activate = ObjectProperty(False)

    def on_activate(self, instance, activate):      # NB muovere tutto in on_press()
        """Ad ogni pressione attivo il bottone se era disattivato o viceversa"""
        if activate is False:
            self.color = [1, 1, 1, 1]
            self.background_color = self.bk_up
        else:
            self.color = self.bk_up
            self.background_color = self.bk_down

    def on_press(self):
        """Eseguo l'evenetuale callback a self.parent_layout e modifico il parametro self.activate"""
        self.activate = not self.activate
        if self.parent_layout:
            self.parent_layout.update_state(self)

    def on_state(self, instance, pressed):
        pass


class DefaultTextInput(TextInput, Writable):
    pass


class DefaultScrollView(ScrollView):
    pass
