from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.properties import ListProperty
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from AppExceptions import *


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
	active = ObjectProperty(False)

	def on_active(self, instance, active):
		"""Ad ogni pressione attivo il bottone se era disattivato o viceversa"""
		if active is True:
			self.background_color = self.bk_active
		else:
			self.background_color = self.bk_inactive

	def on_press(self):
		self.active = not self.active
		if self.parent_layout:
			self.parent_layout.update_state(self)

	def on_state(self, instance, pressed):  # override of DefaultButton.on_state() to not execute that functionality
		pass

	def is_active(self):
		return self.active


class DefaultTextInput(TextInput, Writable):
	def __init__(self, optional=False, field_name="", **kw):
		super().__init__(**kw)
		self.optional = optional
		self.field_name = field_name

	def _get_input(self):
		if not self.text.strip() and self.optional == False:
			raise WrongInputException(f"campo {self.field_name} mancante")

		return self.text.strip()
	
	def get_text(self):
		return self._get_input()

	def get_bool(self):
		text_bool = self._get_input()

		try:
			return bool(int(text_bool))
		except (TypeError, ValueError):
			raise WrongInputException(f"Campo '{self.field_name}' non valido: '{text_bool}'")

	def get_int(self):
		text_int = self._get_input()

		if not text_int:
			return 0

		try:
			int_input = int(text_int)
		except (TypeError, ValueError):
			raise WrongInputException(f"Campo '{self.field_name}' non valido: '{text_int}'")
		else:
			if int_input <= 0:
				raise WrongInputException(f"Campo '{self.field_name}' nullo o negativo")
			return text_int

	def get_float(self):
		text_float = self._get_input()

		if not text_float:
			return 0.

		try:
			float_input = float(text_float)
		except (TypeError, ValueError):
			raise WrongInputException(f"Campo '{self.field_name}' non valido: '{text_float}'")
		else:
			if float_input <= 0:
				raise WrongInputException(f"Campo '{self.field_name}' nullo o negativo")
			return float_input


class DefaultScrollView(ScrollView):
	pass


if __name__ == "__main__":
	pass