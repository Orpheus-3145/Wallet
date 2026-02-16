PATH_SQL_DATA := $(WALLET_DIR)/sql/data/import
PATH_VENV_DIR := $(WALLET_DIR)/wallet_venv
PATH_MAIN := $(WALLET_DIR)/source/main.py
PATH_INIT_WALLET_SCRIPT := $(WALLET_DIR)/bin/init_wallet.sh

PYTHON := $(PATH_VENV_DIR)/bin/python3.12
PIP := $(PATH_VENV_DIR)/bin/pip3.12

all: run

run: $(PATH_VENV_DIR) $(PATH_BACKUP_DIR) $(PATH_LOG_DIR) $(PATH_SQL_DATA)
	source $(PATH_VENV_DIR)/bin/activate && \
	$(PYTHON) $(PATH_MAIN)

$(PATH_VENV_DIR):
	mkdir -p $@
	python3.12 -m venv $(PATH_VENV_DIR) && \
	source $(PATH_VENV_DIR)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

$(PATH_BACKUP_DIR):
	mkdir -p $@

$(PATH_LOG_DIR):
	mkdir -p $@

$(PATH_SQL_DATA):
	mkdir -p $(PATH_SQL_DATA)/import $(PATH_SQL_DATA)/export

export_csv: $(PATH_SQL_DATA)
	./bin/export_data.sh

clean:
	rm -rf $(SOURCE_DIR)/__pycache__
	rm -rf $(PATH_VENV_DIR)
	rm -rf $(PATH_LOG_DIR)/*

re: clean run

.PHONY: all run clean re