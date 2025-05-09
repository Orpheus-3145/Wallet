-include config/wallet.env
-include config/database.env

PYTHON = $(PATH_VENV_DIR)/bin/python3.12
PIP = $(PATH_VENV_DIR)/bin/pip3.12

GREEN = \x1b[32;01m
YELLOW = \x1b[33;01m
BOLD = \033[1m
RESET = \x1b[0m

all: run

run: $(PATH_VENV_DIR) $(PATH_BACKUP_DIR) $(PATH_LOG_DIR) $(PATH_SQL_DATA)
	@source $(PATH_VENV_DIR)/bin/activate && \
	$(PYTHON) $(PATH_MAIN)

$(PATH_VENV_DIR):
	@mkdir -p $@
	@python3.12 -m venv $(PATH_VENV_DIR) && \
	source $(PATH_VENV_DIR)/bin/activate
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@printf "$(GREEN)Virtual environment created in $(BOLD)$(PATH_VENV_DIR)$(RESET)\n"

$(PATH_BACKUP_DIR):
	@mkdir -p $@
	@printf "$(GREEN)Backup folder created$(RESET)\n"

$(PATH_LOG_DIR):
	@mkdir -p $@
	@printf "$(GREEN)Log folder created$(RESET)\n"

$(PATH_SQL_DATA):
	@mkdir -p $(PATH_SQL_DATA)/import $(PATH_SQL_DATA)/export

export_csv: $(PATH_SQL_DATA)
	@./bin/export_data.sh

clean:
	@rm -rf $(SOURCE_DIR)/__pycache__
	@rm -rf $(PATH_VENV_DIR)
	@rm -rf $(PATH_LOG_DIR)/*
	@printf "$(YELLOW)Cleaned virtual cache and environment$(RESET)\n"

re: clean run

.PHONY: all run clean re