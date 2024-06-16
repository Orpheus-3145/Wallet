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
    # def __init__(self, type_payments, **kw):
    #     super().__init__(**kw)
    #     self.type_payments = type_payments
    #     self.refresh_data()

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

    def set_payment(self, btn_instance):
        pass
        # """Aggiungo/rimuovo il pagmento selzionato a main_mov_dict"""
        # id_pag = Tools.get_key_from_dict(self._payments_dict, btn_instance.text)
        # if "ID_PAG" in App.get_running_app().main_mov_dict.keys() and id_pag == App.get_running_app().main_mov_dict["ID_PAG"]:
        #     App.get_running_app().main_mov_dict.pop("ID_PAG")
        # else:
        #     App.get_running_app().main_mov_dict["ID_PAG"] = id_pag


class LayoutSpesaGenerica(LayoutInfo):
    """Layout di inserimento delle informazioni del movimento di tipo spesa generica; _type_spec_movements_dict è un
    dizionario che contiene tutti i possibili tipi di tipi specifici di spesa selezionabili, nella forma
    id_spesa: nome_spesa, popolato in self.refresh_dynamic_objs()"""
    def __init__(self, type_spec_mov, **kw):
        super().__init__(**kw)
        self.type_spec_mov = type_spec_mov
        self.ids.input_tipo_spesa.update_layout(self.type_spec_mov)

    def set_spec_movement(self, btn_instance):
        pass
        """Aggiungo/rimuovo il tipo di spesa selezionata a spec_mov_dict"""
        # tipo_spesa = btn_instance.text
        # if "TIPO_SPESA" in App.get_running_app().spec_mov_dict.keys() and tipo_spesa == App.get_running_app().spec_mov_dict["ID_TIPO_SPESA"]:
        #     App.get_running_app().spec_mov_dict.pop("TIPO_SPESA")
        # else:
        #     App.get_running_app().spec_mov_dict["TIPO_SPESA"] = tipo_spesa


class LayoutSpesaFissa(LayoutInfo):
    """Layout di inserimento delle informazioni del movimento di tipo spesa fissa (descrizione)"""
    pass


class LayoutStipendio(LayoutInfo):
    """Layout di inserimento delle informazioni del movimento di tipo stipendio"""
    pass


class LayoutEntrata(LayoutInfo):
    """Layout di inserimento delle informazioni del movimento di tipo entrata"""
    def __init__(self, type_entrate, **kw):
        super().__init__(**kw)
        self.type_entrate = type_entrate
        self.ids.input_tipo_entrata.update_layout(self.type_entrate)

    def set_tipo_entrata(self, btn_instance):
        """Aggiungo/rimuovo il tipo di entrata selezionata a spec_mov_dict"""
        id_ent = Tools.get_key_from_dict(self._type_entrate_dict, btn_instance.text)
        if "ID_TIPO_ENTRATA" in App.get_running_app().spec_mov_dict and id_ent == App.get_running_app().spec_mov_dict["ID_TIPO_ENTRATA"]:
            App.get_running_app().spec_mov_dict.pop("ID_TIPO_ENTRATA")
        else:
            App.get_running_app().spec_mov_dict["ID_TIPO_ENTRATA"] = id_ent


class LayoutDebitoCredito(LayoutInfo):
    # def __init__(self, **kw):
    #     super().__init__(**kw)
    #     self._deb_cred_list = ["DEBITO", "CREDITO"]
    #     self.refresh_data()

    def set_deb_cred(self, btn_instance):
        pass

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
    """Layout di inserimento delle informazioni del movimento di tipo spesa di mantenimento"""
    pass


class LayoutSpesaViaggio(LayoutInfo):
    """Layout di inserimento delle informazioni del movimento di tipo spesa di viaggio"""
    pass

