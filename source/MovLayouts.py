from DefaultLayouts import *
from kivy.factory import Factory
from datetime import datetime, date
import Tools

class InputParser:

	def parse_text(self, text_input: str, field_name: str):
		if not text_input.strip():
			raise WrongInputException(f"Campo '{field_name}' vuoto")
		
		return text_input.strip()

	def parse_bool(self, bool_input: str, field_name: str):
		if not bool_input.strip():
			raise WrongInputException(f"Campo '{field_name}' vuoto")

		try:
			return bool(int(bool_input.strip()))
		
		except (TypeError, ValueError):
			raise WrongInputException(f"Campo '{field_name}' non valido: '{bool_input}'")

	def parse_int(self, int_input: str, field_name: str, check_positivity=True):
		if not int_input.strip():
			raise WrongInputException(f"Campo '{field_name}' vuoto")

		try:
			int_value = int(int_input.strip())
		
		except (TypeError, ValueError):
			raise WrongInputException(f"Campo '{field_name}' non valido: '{int_input}'")
		
		else:
			if check_positivity is True and int_value <= 0:
				raise WrongInputException(f"Campo '{field_name}' nullo o negativo")
			
			return int_value

	def parse_float(self, float_input: str, field_name: str, check_positivity=True):
		if not float_input.strip():
			raise WrongInputException(f"Campo '{field_name}' vuoto")

		try:
			float_value = float(float_input.strip())
		
		except (TypeError, ValueError):
			raise WrongInputException(f"Campo '{field_name}' non valido: '{float_input}'")
		
		else:
			if check_positivity is True and float_value <= 0:
				raise WrongInputException(f"Campo '{field_name}' nullo o negativo")

			return float_value

	def parse_date(self, y_input: str, m_input: str, d_input: str, set_default_values=True):
		try:
			if set_default_values is True and not y_input.strip():
				year = datetime.now().year
			else:
				year = int(y_input.strip())
			
			if set_default_values is True and not m_input.strip():
				month = datetime.now().month
			else:
				month = int(m_input.strip())
			
			if set_default_values is True and not d_input.strip():
				day = datetime.now().day
			else:
				day = int(d_input.strip())
			
			return date(year, month, day)
		
		except ValueError:
			raise WrongInputException(f"Data non valida: '{d_input}/{m_input}/{y_input}'")


class LayoutInfo(DefaultLayout, BKGrowLayout, InputParser):
	def __init__(self, feeder=None, **kw):
		super().__init__(**kw)
		self.feeder = feeder        # function to call to get updated data

	def get_data(self):
		pass

	def refresh_data(self):
		pass


class LayoutDate(LayoutInfo):

	def get_data(self):
		year = self.ids.input_year.text
		month = self.ids.input_month.text
		day = self.ids.input_day.text
		
		return {"data_mov": self.parse_date(year, month, day)}

	def refresh_data(self):
		self.ids.input_day.text = ""
		self.ids.input_month.text = ""
		self.ids.input_year.text = ""


class LayoutMainMov(LayoutInfo):

	def get_data(self):
		data_info = {}
		if self.ids.input_importo.text:
			data_info["importo"] = self.parse_float(self.ids.input_importo.text, "importo")
		
		if self.ids.input_payments.id_active_widgets():
			data_info["id_conto"] = self.parse_int(self.ids.input_payments.id_active_widgets(), "conto corrente")
		
		if self.ids.input_note.text:
			data_info["note"] = self.parse_text(self.ids.input_note.text, "note")
	
		return data_info

	def refresh_data(self):
		try:
			dynamic_content = self.feeder()
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.ids.input_importo.text = ""
			self.ids.input_payments.update_layout(dynamic_content)
			self.ids.input_note.text = ""


class LayoutSpesaVaria(LayoutInfo):

	def get_data(self):
		data_info = {}
		if self.ids.input_tipo_spesa.id_active_widgets():
			data_info["id_tipo_s_varia"] = self.parse_int(self.ids.input_tipo_spesa.id_active_widgets(), "tipo di spesa")
		
		if self.ids.input_descrizione.text:
			data_info["descrizione"] = self.parse_text(self.ids.input_descrizione.text, "descrizione")
		
		return data_info

	def refresh_data(self):
		try:
			dynamic_content = self.feeder()
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.ids.input_tipo_spesa.update_layout(dynamic_content)
			self.ids.input_descrizione.text = ""


class LayoutSpesaFissa(LayoutInfo):

	def get_data(self):
		return {"descrizione": self.parse_text(self.ids.input_descrizione.text, "descrizione")}

	def refresh_data(self):
		self.ids.input_descrizione.text = ""


class LayoutStipendio(LayoutInfo):

	def get_data(self):
		data_info = {}
		if self.ids.input_ddl.text:
			data_info["ddl"] = self.parse_text(self.ids.input_ddl.text, "datore di lavoro")

		if self.ids.input_lordo.text:
			data_info["lordo"] = self.parse_float(self.ids.input_lordo.text, "lordo")

		if self.ids.input_r_spese.text:
			data_info["rimborso_spese"] = self.parse_float(self.ids.input_r_spese.text, "rimborso_spese")
		
		return data_info

	def refresh_data(self):
		self.ids.input_lordo.text = ""
		self.ids.input_r_spese.text = ""
		self.ids.input_ddl.text = ""


class LayoutEntrata(LayoutInfo):

	def get_data(self):
		data_info = {}
		if self.ids.input_tipo_entrata.id_active_widgets():
			data_info["id_tipo_entrata"] = self.parse_int(self.ids.input_tipo_entrata.id_active_widgets(), "tipo di entrata")

		if self.ids.input_descrizione.text:
			data_info["descrizione"] = self.parse_text(self.ids.input_descrizione.text, "descrizione")

		return data_info

	def refresh_data(self):
		try:
			dynamic_content = self.feeder()
		except AppException as error:
			Factory.ErrorPopup(err_text=str(error)).open()
		else:
			self.ids.input_tipo_entrata.update_layout(dynamic_content)
			self.ids.input_descrizione.text = ""


class LayoutDebitoCredito(LayoutInfo):

	def get_data(self):
		data_info = {}
		if self.ids.input_deb_cred.id_active_widgets():
			data_info["deb_cred"] = self.parse_bool(self.ids.input_deb_cred.id_active_widgets(), "debito/credito")
		
		if self.ids.input_origine.text or "origine" not in fields_not_mandatory:
			data_info["origine"] = self.parse_text(self.ids.input_origine.text, "origine")
		
		if self.ids.input_descrizione.text or "descrizione" not in fields_not_mandatory:
			data_info["descrizione"] = self.parse_text(self.ids.input_descrizione.text, "descrizione")
		
		return data_info

	def refresh_data(self):
		self.ids.input_deb_cred.update_layout({"0": "DEBITO", "1": "CREDITO"})
		self.ids.input_origine.text = ""
		self.ids.input_descrizione.text = ""


class LayoutSaldoDebitoCredito(LayoutInfo):

	def __init__(self, **kw):
		super().__init__(**kw)
		self.ids_deb_cred = []

	def set_data(self, selected_ids):
		self.ids_deb_cred = selected_ids

	def get_data(self):
		return {"id_saldo_deb_cred": Tools.list_to_str(self.ids_deb_cred)}

	def refresh_data(self):
		self.ids_deb_cred.clear()


class LayoutSpesaMantenimento(LayoutInfo):

	def get_data(self):
		return {"descrizione": self.parse_text(self.ids.input_descrizione.text, "descrizione")}

	def refresh_data(self):
		self.ids.input_descrizione.text = ""


class LayoutSpesaViaggio(LayoutInfo):

	def get_data(self):
		data_info = {}

		if self.ids.input_viaggio.text:
			data_info["viaggio"] = self.parse_text(self.ids.input_viaggio.text, "viaggio")

		if self.ids.input_descrizione.text:
			data_info["descrizione"] = self.parse_text(self.ids.input_descrizione.text, "descrizione")
		
		return data_info

	def refresh_data(self):
		self.ids.input_viaggio.text = ""
		self.ids.input_descrizione.text = ""


if __name__ == "__main__":
	pass