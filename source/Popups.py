from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.properties import ObjectProperty


class ErrorPopup(Popup):
    def __init__(self, err_text, func_to_exec=None, **kw):
        super().__init__(**kw)
        self.err_text = err_text
        self.func_to_exec = func_to_exec

    def on_pre_open(self):
        self.ids.lbl_error.text = self.err_text

    def exec_function(self):
        if self.func_to_exec:
            self.func_to_exec()
        self.dismiss()


class SingleChoicePopup(ModalView):
    def __init__(self, info, func_to_exec=None, **kw):
        super().__init__(**kw)
        self.info = info
        self.func_to_exec = func_to_exec

    def on_pre_open(self):
        self.ids.lbl_info.text = self.info

    def exec_function(self):
        if self.func_to_exec:
            self.func_to_exec()
        self.dismiss()


class DoubleChoicePopup(ModalView):
    def __init__(self, info, func_to_exec=None, second_func_to_exec=None, **kw):
        super().__init__(**kw)
        self.info = info
        self.func_to_exec = func_to_exec
        self.second_func_to_exec = second_func_to_exec

    def on_pre_open(self):
        self.ids.lbl_info.text = self.info

    def exec_function(self):
        if self.func_to_exec:
            self.func_to_exec()
        self.dismiss()

    def exec_second_function(self):
        if self.second_func_to_exec:
            self.second_func_to_exec()
        self.dismiss()


if __name__ == "__main__":
    pass