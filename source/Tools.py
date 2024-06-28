# def get_key_from_dict(dictionary, value):
#     """Restituisce la chiave del dizionario tramite il valore passato"""
#     key_list = list(dictionary.keys())
#     value_list = list(dictionary.values())
#
#     return key_list[value_list.index(value)]
import os.path


def convert_to_float(str_number):
    """Questa funzione riceve una stringa che rappresenta un float e, se presenti virgole, le sostituisce con i punti;
    eventualmente restituisce la stringa convertita in int o float"""
    return float(str(str_number).replace(",", "."))


def get_abs_path(relative_path):
    abs_path = os.path.normpath(os.path.join(os.getcwd(), relative_path))
    if os.path.exists(abs_path) is False:
        raise ValueError("non-existing path: {}".format(abs_path))
    return abs_path


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


def str_to_list_float(string_list):
    try:
        return [float(value) for value in string_list[1:-1].split(",")]
    except (TypeError, ValueError, IndexError):
        raise ValueError("invalid format [usage: '[a, b, c, ..., k]']")


if __name__ == "__main__":
    pass
