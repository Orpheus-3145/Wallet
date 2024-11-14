import csv

def read_csv(file_path):
    # Leggi il file CSV e restituisci i dati come una lista di dizionari
    with open(file_path, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        data = list(reader)
    return data

def modify_field(data, field_name, old_value, new_value):
    # Modifica un campo specifico nei dati basato sul criterio di old_value
    for row in data:
        if row.get(field_name) == old_value:
            row[field_name] = new_value
    return data

def write_csv(file_path, data):
    # Scrivi i dati modificati di nuovo nel file CSV
    with open(file_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

# Percorso del file CSV
file_path = 'example.csv'

# Leggi il contenuto del file
data = read_csv(file_path)

# Esegui la modifica
field_name = 'campo_da_modificare'  # Nome del campo
old_value = 'valore_vecchio'  # Valore da cercare
new_value = 'valore_nuovo'  # Nuovo valore da sostituire
data = modify_field(data, field_name, old_value, new_value)

# Scrivi i dati modificati nel file CSV
write_csv(file_path, data)

print("File CSV aggiornato con successo.")