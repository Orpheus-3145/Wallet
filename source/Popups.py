from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.properties import ObjectProperty


class ErrorPopup(Popup):
    """Popop che compare al verificarsi di errori, il parametro err_text contiene informazioni sull'anomalia
    verificatasi"""
    err_text = ObjectProperty("")
    # def __init__(self, err_text="", **kw):      # se e object property funziona
    #     super().__init__(**kw)
    #     self.err_text = err_text


class InfoPopup(ModalView):  # ModalView e non Popup perchè in questo caso non uso non mi serve il titolo
    """- info -> avviso del layout (va nel titolo)
        - func_to_exec -> se <> None viene eseguita quando si preme il bottone con scritto OK"""
    info = ObjectProperty("")
    func_to_exec = ObjectProperty(None)

    def exec_function(self):
        self.dismiss()
        if self.func_to_exec:
            self.func_to_exec()


class SingleChoicePopup(InfoPopup):
    """solo un bottone da premere, oltre alla descrizione"""
    pass


class DoubleChoicePopup(InfoPopup):
    """scelta del tipo 'annulla'/'procedi'"""
    second_func_to_exec = ObjectProperty(None)

    def exec_second_function(self):
        self.dismiss()
        if self.second_func_to_exec:
            self.second_func_to_exec()

