def get_key_from_dict(dictionary, value):
    """Restituisce la chiave del dizionario tramite il valore passato"""
    key_list = list(dictionary.keys())
    value_list = list(dictionary.values())

    return key_list[value_list.index(value)]


def convert_to_float(str_number):
    """Questa funzione riceve una stringa che rappresenta un float e, se presenti virgole, le sostituisce con i punti;
    eventualmente restituisce la stringa convertita in int o float"""
    return float(str(str_number).replace(",", "."))


def escape_sql_chars(string):
    """Esegue l'escaping dei caratteri problematici per le stringe SQL , per esempio il carattere ' """
    return string.replace("'", "''")


def list_to_str(container):     # NB sortare i valori
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
