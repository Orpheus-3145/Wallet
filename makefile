VENV_DIR = wallet_venv
LOG_DIR = logs
BACKUP_DIR = backup
SOURCE_DIR = source

PYTHON = $(VENV_DIR)/bin/python3.12
PIP = $(VENV_DIR)/bin/pip3.12
MAIN = $(SOURCE_DIR)/WalletApp.py

GREEN = \x1b[32;01m
YELLOW = \x1b[33;01m
BOLD = \033[1m
RESET = \x1b[0m

all: run

run: $(VENV_DIR) $(BACKUP_DIR) $(LOG_DIR)
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(MAIN)

$(VENV_DIR):
	@mkdir -p $@
	@python3.12 -m venv $(VENV_DIR) && \
	source $(VENV_DIR)/bin/activate
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@printf "$(GREEN)Virtual environment created in $(BOLD)$(VENV_DIR)$(RESET)\n"

$(BACKUP_DIR):
	@mkdir -p $@
	@printf "$(GREEN)Backup folder created$(RESET)\n"

$(LOG_DIR):
	@mkdir -p $@
	@printf "$(GREEN)Log folder created$(RESET)\n"

clean:
	@rm -rf $(SOURCE_DIR)/__pycache__
	@rm -rf $(VENV_DIR)
	@rm -rf $(LOG_DIR)/*
	@printf "$(YELLOW)Cleaned virtual cache and environment$(RESET)\n"

re: clean run

.PHONY: all run clean re