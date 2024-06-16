from DefaultLayouts import *
from kivy.app import App
import Tools


class LayoutInfo(DefaultLayout, BKGrowLayout):
    """Schermata che permette di inserire una data nel formato giorno-mese-anno, salvati in 3 variabili indipendenti"""
    def get_data(self):
        pass

    def refresh_data(self, new_data=None):
        pass


class LayoutDate(LayoutInfo):
    def get_data(self):
        data = {}
        if self.ids.input_day.text.strip() and self.ids.input_month.text.strip() and self.ids.input_year.text.strip():
            data["str_data_mov"] = "{}/{}/{}".format(self.ids.input_day.text.strip(),
                                                     self.ids.input_month.text.strip(),
                                                     self.ids.input_year.text.strip())
        return data

    def refresh_data(self, new_data=None):
        self.ids.input_day.text = ""
        self.ids.input_month.text = ""
        self.ids.input_year.text = ""


class LayoutMainMov(LayoutInfo):
    """Layout di inserimento delle informazioni generiche del movimento, il parametro _payments_dict è un dizionario che
    contiene tutti i possibili tipi di pagamento selezionabili nella forma id_pagamento: nome_pagamento, popolato
    in self.refresh_dynamic_objs()"""
    def get_data(self):
        data = {}
        if self.ids.input_importo.text.strip():
            data["importo"] = self.ids.input_importo.text.strip()
        if self.ids.input_payments.get_selected_value():
            data["type_pag"] = self.ids.input_payments.get_selected_value()
        if self.ids.input_note.text.strip():
            data["note"] = self.ids.input_note.text.strip()
        return data

    def refresh_data(self, new_data=None):
        self.ids.input_importo.text = ""
        self.ids.input_payments.update_layout(new_data)
        self.ids.input_note.text = ""


class LayoutSpesaGenerica(LayoutInfo):
    """Layout di inserimento delle informazioni del movimento di tipo spesa generica; _type_spec_movements_dict è un
    dizionario che contiene tutti i possibili tipi di tipi specifici di spesa selezionabili, nella forma
    id_spesa: nome_spesa, popolato in self.refresh_dynamic_objs()"""
    def get_data(self):
        data = {}
        if self.ids.input_tipo_spesa.get_selected_value():
            data["type_s_varia"] = self.ids.input_tipo_spesa.get_selected_value()
        if self.ids.input_descrizione.text.strip():
            data["descrizione"] = self.ids.input_descrizione.text.strip()
        return data

    def refresh_data(self, new_data=None):
        self.ids.input_tipo_spesa.update_layout(new_data)
        self.ids.input_descrizione.text = ""


class LayoutSpesaFissa(LayoutInfo):
    """Layout di inserimento delle informazioni del movimento di tipo spesa fissa (descrizione)"""
    def get_data(self):
        data = {}
        if self.ids.input_descrizione.text.strip():
            data["descrizione"] = self.ids.input_descrizione.text.strip()
        return data

    def refresh_data(self, new_data=None):
        self.ids.input_descrizione.text = ""


class LayoutStipendio(LayoutInfo):
    def get_data(self):
        data = {}
        if self.ids.input_netto.text.strip():
            data["netto"] = self.ids.input_netto.text.strip()
        if self.ids.input_r_spese.text.strip():
            data["rimborso_spese"] = self.ids.input_r_spese.text.strip()
        if self.ids.input_ddl.text.strip():
            data["ddl"] = self.ids.input_ddl.text.strip()
        if self.ids.input_note.text.strip():
            data["note"] = self.ids.input_note.text.strip()
        return data

    def refresh_data(self, new_data=None):
        self.ids.input_netto.text = ""
        self.ids.input_r_spese.text = ""
        self.ids.input_ddl.text = ""


class LayoutEntrata(LayoutInfo):
    """Layout di inserimento delle informazioni del movimento di tipo entrata"""
    def get_data(self):
        data = {}
        if self.ids.input_tipo_entrata.get_selected_value():
            data["type_entrata"] = self.ids.input_tipo_entrata.get_selected_value()
        if self.ids.input_descrizione.text.strip():
            data["descrizione"] = self.ids.input_descrizione.text.strip()
        return data

    def refresh_data(self, new_data=None):
        self.ids.input_tipo_entrata.update_layout(new_data)
        self.ids.input_descrizione.text = ""


class LayoutDebitoCredito(LayoutInfo):
    def get_data(self):
        data = {}
        if self.ids.input_deb_cred.get_selected_value():
            if self.ids.input_deb_cred.get_selected_value() == "DEBITO":
                data["deb_cred"] = 0
            else:
                data["deb_cred"] = 1
        if self.ids.input_origine.text.strip():
            data["origine"] = self.ids.input_origine.text.strip()
        if self.ids.input_descrizione.text.strip():
            data["descrizione"] = self.ids.input_descrizione.text.strip()
        return data

    def refresh_data(self, new_data=None):
        self.ids.input_deb_cred.update_layout(["DEBITO", "CREDITO"])
        self.ids.input_origine.text = ""
        self.ids.input_descrizione.text = ""


class LayoutSpesaMantenimento(LayoutInfo):
    def get_data(self):
        data = {}
        if self.ids.input_descrizione.text.strip():
            data["descrizione"] = self.ids.input_descrizione.text.strip()
        return data

    def refresh_data(self, new_data=None):
        self.ids.input_descrizione.text = ""


class LayoutSpesaViaggio(LayoutInfo):
    def get_data(self):
        data = {}
        if self.ids.input_viaggio.text.strip():
            data["viaggio"] = self.ids.input_viaggio.text.strip()
        if self.ids.input_descrizione.text.strip():
            data["descrizione"] = self.ids.input_descrizione.text.strip()
        return data

    def refresh_data(self, new_data=None):
        self.ids.input_viaggio.text = ""
        self.ids.input_descrizione.text = ""

