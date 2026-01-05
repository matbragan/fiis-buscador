.PHONY: setup install run format lint check

setup:
	python3 -m venv .venv
	@echo "✓ Virtual environment created!"

install:
	@.venv/bin/python -m pip install --upgrade pip
	@.venv/bin/python -m pip install -r requirements.txt
	@.venv/bin/python -m pip install -e .
	@echo "✓ Dependencies installed!"

run:
	@.venv/bin/python -m streamlit run buscador.py

format:
	@.venv/bin/python -m black .
	@.venv/bin/python -m isort .

lint:
	-@.venv/bin/python -m flake8 .  || echo "✗ Flake8 issues found"

check: format lint
