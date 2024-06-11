from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.properties import ListProperty
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView


class BKG(Widget):
    border_color = ListProperty([1, 1, 1, 1])


class BKGlabel(BKG):
    background_color = ListProperty([1, 1, 1, 1])


class BKGrowLayout(BKG):
    pass


class DefaultLabel(Label, BKGlabel):
    pass


class DefaultButton(Button):
    parent_layout = ObjectProperty(None)       # NB move non static member non objectproperty

    def on_state(self, instance, pressed):
        if pressed == "down":
            if self.parent_layout:
                self.parent_layout.btn_pressed(self)
            self.background_color.pop()
            self.background_color.append(0.75)

        else:
            self.background_color.pop()
            self.background_color.append(1)


class DefaultSelectionButton(Button):
    """Bottone che rimane attivo una volta premuto, self.activate segnala se esso è attivo o meno, vedi DefaultButton
    per self.parent_layout"""
    activate = ObjectProperty(False)
    parent_layout = ObjectProperty(None)       # NB move non static member non objectproperty
    tmp_color = [1, 1, 1, 1]

    def on_activate(self, instance, activate):
        """Ad ogni pressione attivo il bottone se era disattivato o viceversa"""
        if activate is False:
            self.color = [1, 1, 1, 1]
            self.background_color = self.tmp_color
        else:
            self.color = self.background_color
            self.tmp_color = self.background_color
            self.background_color = [0, 1, 0, 1]

    def on_press(self):
        """Eseguo l'evenetuale callback a self.parent_layout e modifico il parametro self.activate"""
        if self.parent_layout:
            self.parent_layout.btn_pressed(self)
        self.activate = not self.activate


class DefaultTextInput(TextInput):
    """TextInput standard, definito in DefaultWidgets.kv"""
    pass


class DefaultScrollView(ScrollView):
    """Lo dichiaro per settare alcuni valori fissi in DefaultWidgets.kv"""
    pass
