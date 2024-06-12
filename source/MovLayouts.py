from DefaultLayouts import *
from kivy.app import App
import Tools


class LayoutData(DefaultLayout, BKGrowLayout):
    """Schermata che permette di inserire una data nel formato giorno-mese-anno, salvati in 3 variabili indipendenti"""
    pass


class LayoutMainMov(DefaultLayout, BKGrowLayout):
    """Layout di inserimento delle informazioni generiche del movimento, il parametro _payments_dict è un dizionario che
    contiene tutti i possibili tipi di pagamento selezionabili nella forma id_pagamento: nome_pagamento, popolato
    in self.refresh_dynamic_objs()"""
    def __init__(self, type_payments, **kw):
        super().__init__(**kw)
        self._payments_dict = type_payments
        self.ids.input_payments.update_layout(type_payments.values())

    def set_payment(self, btn_instance):
        """Aggiungo/rimuovo il pagmento selzionato a main_mov_dict"""
        id_pag = Tools.get_key_from_dict(self._payments_dict, btn_instance.text)
        if "ID_PAG" in App.get_running_app().main_mov_dict.keys() and id_pag == App.get_running_app().main_mov_dict["ID_PAG"]:
            App.get_running_app().main_mov_dict.pop("ID_PAG")
        else:
            App.get_running_app().main_mov_dict["ID_PAG"] = id_pag


class LayoutSpesaGenerica(DefaultLayout, BKGrowLayout):
    """Layout di inserimento delle informazioni del movimento di tipo spesa generica; _type_spec_movements_dict è un
    dizionario che contiene tutti i possibili tipi di tipi specifici di spesa selezionabili, nella forma
    id_spesa: nome_spesa, popolato in self.refresh_dynamic_objs()"""
    def __init__(self, mov_list, **kw):
        super().__init__(**kw)
        self._type_spec_movements_dict = mov_list
        self.ids.input_tipo_spesa.update_layout(mov_list.values())

    def set_spec_movement(self, btn_instance):
        """Aggiungo/rimuovo il tipo di spesa selezionata a spec_mov_dict"""
        id_spesa = Tools.get_key_from_dict(self._type_spec_movements_dict, btn_instance.text)
        if "ID_TIPO_SPESA" in App.get_running_app().spec_mov_dict.keys() and id_spesa == App.get_running_app().spec_mov_dict["ID_TIPO_SPESA"]:
            App.get_running_app().spec_mov_dict.pop("ID_TIPO_SPESA")
        else:
            App.get_running_app().spec_mov_dict["ID_TIPO_SPESA"] = id_spesa


class LayoutSpesaFissa(DefaultLayout, BKGrowLayout):
    """Layout di inserimento delle informazioni del movimento di tipo spesa fissa (descrizione)"""
    pass


class LayoutStipendio(DefaultLayout, BKGrowLayout):
    """Layout di inserimento delle informazioni del movimento di tipo stipendio"""
    pass


class LayoutEntrata(DefaultLayout, BKGrowLayout):
    """Layout di inserimento delle informazioni del movimento di tipo entrata"""
    def __init__(self, type_entrate, **kw):
        super().__init__(**kw)
        self._type_entrate_dict = type_entrate
        self.ids.input_tipo_entrata.update_layout(type_entrate.values())

    def set_tipo_entrata(self, btn_instance):
        """Aggiungo/rimuovo il tipo di entrata selezionata a spec_mov_dict"""
        id_ent = Tools.get_key_from_dict(self._type_entrate_dict, btn_instance.text)
        if "ID_TIPO_ENTRATA" in App.get_running_app().spec_mov_dict.keys() and id_ent == App.get_running_app().spec_mov_dict["ID_TIPO_ENTRATA"]:
            App.get_running_app().spec_mov_dict.pop("ID_TIPO_ENTRATA")
        else:
            App.get_running_app().spec_mov_dict["ID_TIPO_ENTRATA"] = id_ent


class LayoutDebitoCredito(DefaultLayout, BKGrowLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._deb_cred_list = ["DEBITO", "CREDITO"]
        self.ids.input_deb_cred.update_layout(self._deb_cred_list)

    def set_deb_cred(self, btn_instance):
        """Aggiorno spec_mov_dict con il tipo scelto: debito o credito"""
        deb_cred = btn_instance.text
        if deb_cred in self._deb_cred_list:
            App.get_running_app().spec_mov_dict["DEBCRED"] = "1" if deb_cred == "CREDITO" else "0"


class LayoutSaldoDebitoCredito(DefaultLayout, BKGrowLayout):
    """Layout di inserimento delle informazioni per saldare uno o più debiti/crediti esistenti; il parametro
    _payments_dict è un dizionario che contiene tutti i possibili tipi di pagamento selezionabili nella forma
    id_pagamento: nome_pagamento, popolato in self.refresh_dynamic_objs()"""
    def __init__(self, type_payments, **kw):
        super().__init__(**kw)
        self._payments_dict = type_payments
        self.ids.input_payments.update_layout(type_payments.values())

    def set_payment(self, btn_instance):
        """Aggiungo/rimuovo il pagmento selzionato a main_mov_dict"""
        id_pag = Tools.get_key_from_dict(self._payments_dict, btn_instance.text)
        if "ID_PAG" in App.get_running_app().main_mov_dict.keys() and id_pag == App.get_running_app().main_mov_dict["ID_PAG"]:
            App.get_running_app().main_mov_dict.pop("ID_PAG")
        else:
            App.get_running_app().main_mov_dict["ID_PAG"] = id_pag


class LayoutSpesaMantenimento(DefaultLayout, BKGrowLayout):
    """Layout di inserimento delle informazioni del movimento di tipo spesa di mantenimento"""
    pass


class LayoutSpesaViaggio(DefaultLayout, BKGrowLayout):
    """Layout di inserimento delle informazioni del movimento di tipo spesa di viaggio"""
    pass

