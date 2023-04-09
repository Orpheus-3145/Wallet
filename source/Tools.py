from datetime import datetime, date
import logging
import os
from win32api import GetSystemMetrics


class WrongSQLstatement(Exception):
    """Eccezione che viene sollevata in caso in cui il comando SQL non sia creato correttamente"""

    def __init__(self, error_text):
        super().__init__()
        self.error_text = error_text  # creo la proprietà di classe per avere maggiori informazioni sull'errore verificatosi

    def __str__(self):
        return self.error_text


def format_sql_string(suide,
                      table_name=None,
                      field_select_list=None,
                      where_dict=None,
                      update_dict=None,
                      insert_dict=None,
                      join_type=None,
                      join_table=None,
                      join_dict=None,
                      varchar_values=None,
                      order_by_dict=None,
                      top=None,
                      proc_name=None,
                      proc_args_dict=None):

    """Crea e formatta un'instruzione SQL di tipo suid (SELECT, UPDATE, INSERT, DELETE)
        - suid -> ha come valore 'S' SELECT, 'U' UPDATE, 'I' INSERT, 'D' DELETE, 'E' EXEC (esegue procedura)
        - table_name -> nome della tabella in questione,
        - field_select_list -> lista di campi da selezionare/modificare/inserire/cancellare
        - where_dict -> dizionario che contiene n condizioni che devono essere interamente soddisfatte (AND ... AND ... ) nella forma chiave = valore inseriti nel costrutto WHERE
        - update_dict -> dizionario in cui chaive (<-campo) = valore nel costrutto SET di UPDATE
        - insert_dict -> dizionario contenete il campo (chiave) e il valore da inserire in esso nel costrutto INSERT INTO
        - join -> tipo di join da eseguire -> 'I' inner, 'L' left, 'R' right, 'C' cross
        - join_table -> tabella da joinare, NB per ora non sono previsti join multipli
        - join_fields -> dizionario di campi da uguagliare per il join
        - varchar_values -> lista di valori varchar da inserire in select, where, insert o update, restituisce il valore nello statement SQL racchiuso da singoli apici
        - order_by_dict -> coppie CAMPO: DESC/ASC
        - top -> se diverso da None mostra le prime top (int) righe
        - proc_name -> nome procedura da eseguire
        - proc_args_dict -> dizionario nella forma {nome_argomento: valore_argomento}"""

    sql_string = ""
    join_types_dict = {"I": "INNER JOIN", "L": "LEFT JOIN", "R": "RIGHT JOIN", "C": "CROSS JOIN"}

    if suide == 'S':
        sql_string = "SELECT * FROM {}".format(table_name)

        if top is not None:     # inserisco top x nella select
            if str(top).isdigit():
                top_n_values = "top {}".format(int(top))
                sql_string = sql_string.replace("SELECT", "SELECT {}".format(top_n_values))

            else:
                raise WrongSQLstatement("Non è stato passato un valore numerico per il numero di record da selezionare")

        if isinstance(field_select_list, list):  # field_select_list <> None rimuovo '*' e creo l'elenco dei campi
            fields_to_select = ", ".join(field_select_list)
            sql_string = sql_string.replace("*", fields_to_select)

        elif where_dict:
            raise WrongSQLstatement("è stato passato un parametro non valido per la condizione SELECT, deve essere list")

        if join_dict or join_table or join_type:
            if join_type in join_types_dict.keys() and join_table and isinstance(join_dict, dict):       # in questo caso devo inserire anche un join
                fields_to_join = " AND ".join("{} = {}".format(key, value) for key, value in join_dict.items())
                sql_string = " ".join([sql_string, join_types_dict.get(join_type), join_table, "ON", fields_to_join])

            else:
                raise WrongSQLstatement("Nel caso di un join deve essere fornita sia la tabella da legare, sia l'elenco "
                                        "dei cambi da uguagliare, sia il parametro corretto per il tipo di join")

        if isinstance(where_dict, dict):  # se where_dict <> da None aggiungo anche le restrizioni tramite WHERE statement
            fields_to_filter = " AND ".join("{} = {}".format(key,  "'{}'".format(escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in where_dict.items())
            sql_string = " ".join([sql_string, "WHERE", fields_to_filter])

        elif where_dict:
            raise WrongSQLstatement("è stato passato un parametro non valido per la condizione WHERE, deve essere dict")

        if isinstance(order_by_dict, dict):     # se order_by_dict <> da None inserisco l'ordinamento
            fields_to_order_by = ", ".join("{} {}".format(key, value) for key, value in order_by_dict.items())
            sql_string = " ".join([sql_string, "ORDER BY", fields_to_order_by])

        elif order_by_dict:
            raise WrongSQLstatement("è stato passato un parametro non valido per la condizione ORDER BY, deve essere dict")
    elif suide == 'U':
        sql_string = "UPDATE {} SET".format(table_name)

        if isinstance(update_dict, dict):
            fields_to_update = ", ".join("{} = {}".format(key, "'{}'".format(escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in update_dict.items())
            sql_string = " ".join([sql_string, fields_to_update])

        else:
            raise WrongSQLstatement("Non è stata fornita la lista dei campi da modificare oppure il tipo non è corretto, deve essere dict")

        if isinstance(where_dict, dict):  # se where_dict è tipo dict aggiungo anche le restrizioni tramite WHERE statement
            fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in where_dict.items())
            sql_string = " ".join([sql_string, "WHERE", fields_to_filter])

        elif where_dict is not None:
            raise WrongSQLstatement("è stato passato un parametro non valido per la condizione WHERE, deve essere dict")

        else:  # cautela personale per non modificare una tabella per intero
            raise WrongSQLstatement("Non si può modificare interamente una tabella!")
    elif suide == 'I':
        if isinstance(insert_dict, dict):  # mi accerto che venga fornita la lista dei campi e il loro relativo valore da aggiungere
            sql_string = "INSERT INTO {}".format(table_name)
            fields_to_insert = "({})".format(", ".join(insert_dict.keys()))                              # elenco campi da inserire
            values_to_insert = "({})".format(", ".join(["'{}'".format(escape_sql_chars(value)) if varchar_values and value in varchar_values else str(value) for value in insert_dict.values()]))  # elenco valori da inserire

            sql_string = " ".join([sql_string, fields_to_insert, "VALUES", values_to_insert])

        elif insert_dict is not None:
            raise WrongSQLstatement("è stato passato un parametro non valido per la condizione INSERT, deve essere dict")

        else:
            raise WrongSQLstatement("Non è stata fornita la lista dei campi da inserire!")
    elif suide == 'D':
        sql_string = "DELETE {}".format(table_name)

        if isinstance(where_dict, dict):  # non voglio mai cancellare per intero la tabella, faccio sì che debbano esserci sempre clausole WHERE
            fields_to_filter = " AND ".join("{} = {}".format(key, "'{}'".format(escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in where_dict.items())
            sql_string = " ".join([sql_string, "WHERE", fields_to_filter])

        elif where_dict is not None:
            raise WrongSQLstatement("è stato passato un parametro non valido per la condizione WHERE, deve essere dict")

        else:
            raise WrongSQLstatement("Non è possibile eliminare per intero una tabella!")
    elif suide == "E":
        sql_string = "exec {}".format(proc_name)
        if isinstance(proc_args_dict, dict):  # se proc_args_dict <> da None aggiungo anche la lista di argomenti
            args = ", ".join("@{} = {}".format(key,  "'{}'".format(escape_sql_chars(value)) if varchar_values and value in varchar_values else value) for key, value in proc_args_dict.items())
            sql_string = " ".join([sql_string, args])

    return sql_string


def validate_and_set_date(date):
    """Verifica che il dizionario in input contenga una data e la restituisce come istanza di datetime"""
    if not isinstance(date, dict):  # date non è un dizionario
        return None
    elif not date:  # il dizionario è vuoto, restituisce la data odierna
        return datetime.now().strftime("%d-%m-%Y")
    else:
        count = 0  # se arriva a 3 alla fine del ciclo restituisce data odierna, vedi poi
        time_dict = {"day": range(1, 32), "month": range(1, 13), "year": range(2000, 2024)}
        for time_period, time_range in time_dict.items():
            if time_period not in date.keys() or date[time_period].strip() == "":  # se manca l'elemento oppure è vuoto aumento count
                count += 1
            else:  # in caso contrario allora esiste e non è vuoto
                try:
                    if int(date[time_period]) not in time_range:  # se è all'esterno del relativo range il numero non è valido e quindi la data
                        return None
                except (ValueError, TypeError):  # l'elemento non è in formato numerico intero, data non valida
                    return None
        if count == 3:  # se per tre volte l'elemento mancava oppure era vuoto allora restituisce data odierna
            return datetime.now().strftime("%d-%m-%Y")
        elif count == 0:   # crea la data con i tre parametri passati
            return datetime(int(date["year"]), int(date["month"]), int(date["day"])).strftime("%d-%m-%Y")
        else:   # mancano uno o due elementi, data non valida
            return None


def get_key_from_dict(dictionary, value):
    """Restituisce la chiave del dizionario tramite il valore passato"""
    key_list = list(dictionary.keys())
    value_list = list(dictionary.values())

    return key_list[value_list.index(value)]


def replace_coma(str_number, return_type=None):
    """Questa funzione riceve una stringa che rappresenta un float e, se presenti virgole, le sostituisce con i punti;
    eventualmente restituisce la stringa convertita in int o float"""
    str_number = str(str_number)

    if return_type:
        if return_type == int:
            return int(float(str_number.replace(",", ".")))

        elif return_type == float:
            return float(str_number.replace(",", "."))

    else:
        return str_number.replace(",", ".")


def escape_sql_chars(string):
    """Esegue l'escaping dei caratteri problematici per le stringe SQL , per esempio il carattere ' """
    return string.replace("'", "''")


def list_to_str(container):
    """Converte in stringa un contenitore passato (list, dict, ...)"""
    str_elements = ""
    if isinstance(container, list) or isinstance(container, set):
        str_elements += ", ".join([str(element) for element in container])
    elif isinstance(container, dict):
        str_elements += ", ".join("{}: {}".format(key, value) for key, value in container.items())

    return str_elements


def str_to_list(string_list):
    """Da una stringa nel formato '[a, b, c, ...]' restituisce una lista"""
    return [float(element.strip()) for element in string_list[1:len(string_list) - 1].split(",")]


def create_logger(logger_name, log_level, log_name, log_path, fmt):
    """Crea un file di log con livello, percorso, nome e formattazione dei record passati come parametri, richiamando
    poi il modulo logging sarà possibile scrivere su di esso"""
    logger = logging.getLogger(logger_name)
    logging.root = logger
    logger.setLevel(log_level)
    file_handler = logging.FileHandler(filename=os.path.join(log_path, log_name.format(date.today().strftime("%d-%m-%Y"))))
    log_formatter = logging.Formatter(fmt=fmt)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)


def set_center_app(config_obj):
    """A seconda dello schermo che uso, centro l'app nel monitor"""
    width_app = config_obj.getint("graphics", "width")
    height_app = config_obj.getint("graphics", "height")
    width_screen = GetSystemMetrics(0)
    height_screen = GetSystemMetrics(1)
    config_obj.set("graphics", "top", str((height_screen - height_app) // 2))
    config_obj.set("graphics", "left", str((width_screen - width_app) // 2))
    config_obj.write()


# def get_perc_font(len_str, w, h, surface_widget=None, wid_inst=None):
#     """La dimensione del font deve essere in funzione del numero di caratteri della stringa che deve essere inserita in
#     un'etichetta (per evitare tagli), creo quindi una funzione interpolante (polinomiale, metodo di Lagrange) a seconda
#     di alcuni punti (elencati qui sotto) per cui si ha un buon compromesso font_size/lunghezza caratteri"""
#     # nb la dimensione finale è calcolata in base alle dimensioni della label che contiene la stringa, bisogna generalizzare
#     # deve essere in funzione dell'area del widget e della lunghezza della stringa da inserire
#     # interpolazione bilineare!
#     #
#     # 1° coppia (250, 0.32)
#     # 2° coppia (63, 0.5)
#     # 3° coppia (163, 0.37)
#     # 4° coppia (116, 0.42)
#     # 5° coppia (209, 0.324)
#     # 6° coppia (91, 0.45)
#     # 1.7
#     x_0, y_0 = 250, 0.32    # 250 estremo superiore
#     x_1, y_1 = 63, 1.2     # 63 estremo inferiore
#     x_2, y_2 = 163, 0.37    # valore contenuto tra x_0 e x_1
#
#     if len_str < x_1:       # se la lunghezza di len_str è minore dell'estremo inf o maggiore di quello sup. uso valori costanti
#         return y_1
#
#     elif len_str > x_0:
#         return y_0
#
#     else:   # se invece è contenuta nell'intervallo uso la funzione interpolante
#         return y_0 * ((len_str - x_1)/(x_0 - x_1)) * ((len_str - x_2)/(x_0 - x_2)) +\
#                y_1 * ((len_str - x_0)/(x_1 - x_0)) * ((len_str - x_2)/(x_1 - x_2)) +\
#                y_2 * ((len_str - x_0)/(x_2 - x_0)) * ((len_str - x_1)/(x_2 - x_1))


if __name__ == "__main__":
    pass
