VENV_DIR = wallet_venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
SOURCE_DIR = source
MAIN = $(SOURCE_DIR)/WalletApp.py

GREEN := \x1b[32;01m
YELLOW = \x1b[33;01m
RESET := \x1b[0m

all: run

run: build
	@$(PYTHON) $(MAIN)

build: $(VENV_DIR)/bin/activate

$(VENV_DIR)/bin/activate: requirements.txt
	@mkdir -p logs/
	@mkdir -p backup/
	@printf "$(GREEN)Folders logs and backup created$(RESET)\n"
	@python3 -m venv $(VENV_DIR) >/dev/null
	@$(PIP) install --upgrade pip >/dev/null
	@$(PIP) install -r requirements.txt
	@printf "$(GREEN)Virtual environment created$(RESET)\n"

clean:
	@rm -rf $(SOURCE_DIR)/__pycache__
	@rm -rf $(VENV_DIR)
	@printf "$(YELLOW)Cleaned virtual cache and environment$(RESET)\n"

re: clean run

.PHONY: all run build clean re