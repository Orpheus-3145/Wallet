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

    def __init__(self, sql_trace, sql_query=""):
        super().__init__()
        self.sql_trace = sql_trace
        self.sql_query = sql_query      # query SQL che ha causato l'errore

    def __str__(self):
        sql_string_info = ""
        if self.sql_query:
            sql_string_info = "nell'esecuzione stringa SQL: {} ".format(self.sql_query)
        return "Errore database {}- trace: ".format(sql_string_info, self.sql_query)


class InternalError(Exception):
    """Errore generico di natura fatale, non riconducibile all'errore di un utente ma ad un errore del programma
    (esclusi quelli relativi al database e SQL)."""

    def __init__(self, error_text):
        super().__init__()
        self.error_text = error_text

    def __str__(self):
        return self.error_text

