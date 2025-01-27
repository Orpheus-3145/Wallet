from DefaultLayouts import *
from kivy.factory import Factory
from datetime import datetime, date


class LayoutInfo(DefaultLayout, BKGrowLayout):
	def __init__(self, feeder=None, **kw):
		super().__init__(**kw)
		self.feeder = feeder        # function to call to get updated data

	def get_data(self):
		pass

	def refresh_data(self):
		pass


class LayoutDate(LayoutInfo):

	def get_data(self):
		return {"data_mov": self._parse_date()}

	def refresh_data(self):
		self.ids.input_day.text = ""
		self.ids.input_month.text = ""
		self.ids.input_year.text = ""

	def _parse_date(self, set_default_values=True):
		y_input = self.ids.input_year.get_text()
		m_input = self.ids.input_month.get_text()
		d_input = self.ids.input_day.get_text()

		try:
			if set_default_values is True and not y_input:
				year = datetime.now().year
			else:
				year = int(y_input)
			
			if set_default_values is True and not m_input:
				month = datetime.now().month
			else:
				month = int(m_input)
			
			if set_default_values is True and not d_input:
				day = datetime.now().day
			else:
				day = int(d_input)
			
			return date(year, month, day)
		
		except ValueError:
			raise WrongInputException(f"Data non valida: '{d_input}/{m_input}/{y_input}'")


class LayoutMainMov(LayoutInfo):

	def get_data(self, fields_to_skip=[]):
		data_info = {}
		if self.ids.input_importo.text and "importo" not in fields_to_skip:
			data_info["importo"] = self.ids.input_importo.get_float()
		data_info["id_conto"] = self.ids.input_payments.get_id()

		if self.ids.input_note.text:
			data_info["note"] = self.ids.input_note.get_text()
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
		data_info["id_tipo_s_varia"] = self.ids.input_tipo_spesa.get_id()
		data_info["descrizione"] = self.ids.input_descrizione.get_text()
		
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
		return {"descrizione": self.ids.input_descrizione.get_text()}

	def refresh_data(self):
		self.ids.input_descrizione.text = ""


class LayoutStipendio(LayoutInfo):

	def get_data(self):
		data_info = {}
		data_info["ddl"] = self.ids.input_ddl.get_text()

		if self.ids.input_lordo.text:
			data_info["lordo"] = self.ids.input_lordo.get_float()

		if self.ids.input_r_spese.text:
			data_info["rimborso_spese"] = self.ids.input_r_spese.get_float()
		
		return data_info

	def refresh_data(self):
		self.ids.input_lordo.text = ""
		self.ids.input_r_spese.text = ""
		self.ids.input_ddl.text = ""


class LayoutEntrata(LayoutInfo):

	def get_data(self):
		data_info = {}
		data_info["id_tipo_entrata"] = self.ids.input_tipo_entrata.get_id()
		data_info["descrizione"] = self.ids.input_descrizione.get_text()

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
		data_info["deb_cred"] = bool(self.ids.input_deb_cred.get_id())
		data_info["origine"] = self.ids.input_origine.get_text()
		data_info["descrizione"] = self.ids.input_descrizione.get_text()
		
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
		return {"id_saldo_deb_cred": self.ids_deb_cred}

	def refresh_data(self):
		self.ids_deb_cred.clear()


class LayoutSpesaMantenimento(LayoutInfo):

	def get_data(self):
		return {"descrizione": self.ids.input_descrizione.get_text()}

	def refresh_data(self):
		self.ids.input_descrizione.text = ""


class LayoutSpesaViaggio(LayoutInfo):

	def get_data(self):
		data_info = {}
		data_info["viaggio"] = self.ids.input_viaggio.get_text()
		data_info["descrizione"] = self.ids.input_descrizione.get_text()
		
		return data_info

	def refresh_data(self):
		self.ids.input_viaggio.text = ""
		self.ids.input_descrizione.text = ""


if __name__ == "__main__":
	pass