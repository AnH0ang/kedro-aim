#################################################################################
# GLOBALS                                                                       #
#################################################################################
ENVNAME := .venv
VENV := $(ENVNAME)/bin

PROJECT_NAME = {{ package_name }}
PYTHON_INTERPRETER = $(VENV)/python

#################################################################################
# COMMANDS                                                                      #
#################################################################################documentation:

.PHONY: test
test:
	$(VENV)/pytest
	$(VENV)/coverage report

.PHONY: install
install:
	poetry config virtualenvs.in-project true
	poetry install

.PHONY: documentation
documentation:
	$(VENV)/mkdocs serve

.PHONY: lint
lint:
	git add --intent-to-add .
	$(VENV)/pre-commit run --all-files

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

	rm -rf .*_cache
	rm -rf logs
	rm -rf site

	rm -rf .cover*
	rm -rf htmlcov
