class AppException(Exception):
    """Se si verifica un errore interno a livello di funzionamento di widget"""
    def __init__(self, error_text):
        super().__init__()
        self.error_text = error_text  # creo la proprietà di classe per avere maggiori informazioni sull'errore verificatosi

    def __str__(self):
        return self.error_text


class WrongValueInsert(Exception):
    """Eccezione che viene sollevata in caso in cui uno dei dati passati, da inserire in un movimento, non sia corretto"""

    def __init__(self, error_text):
        super().__init__()
        self.error_text = error_text

    def __str__(self):
        return self.error_text


class SqlError(Exception):
    """Errore generico di natura fatale, non riconducibile all'errore di un utente ma ad un errore del programma
    (esclusi quelli relativi al database e SQL)."""

    def __init__(self, sql_trace):
        super().__init__()
        self.sql_trace = sql_trace

    def __str__(self):
        return "Errore database - trace: {}".format(self.sql_trace)


class InternalError(Exception):
    """Errore generico di natura fatale, non riconducibile all'errore di un utente ma ad un errore del programma
    (esclusi quelli relativi al database e SQL)."""

    def __init__(self, error_text):
        super().__init__()
        self.error_text = error_text

    def __str__(self):
        return self.error_text


if __name__ == "__main__":
    pass