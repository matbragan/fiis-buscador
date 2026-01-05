.PHONY: setup install format lint check run

setup:
	@if ! command -v pyenv >/dev/null 2>&1; then \
		echo "✗ pyenv não está instalado. Por favor, instale o pyenv primeiro."; \
		exit 1; \
	fi
	pyenv install $(pyenv local)
	python3 -m venv .venv
	@echo "✓ Ambiente virtual criado!"

install:
	@if [ ! -d ".venv" ]; then \
		echo "✗ Ambiente virtual não encontrado. Por favor, execute 'make setup' primeiro."; \
		exit 1; \
	fi
	@.venv/bin/python -m pip install --upgrade pip
	@.venv/bin/python -m pip install -r requirements.txt
	@.venv/bin/python -m pip install -e .
	@echo "✓ Dependências instaladas!"

format:
	@.venv/bin/python -m black .
	@.venv/bin/python -m isort .
	@echo "✓ Código formatado!"

lint:
	@.venv/bin/python -m flake8 . || echo "✗ Problemas de lint encontrados!"

check: format lint

run:
	@.venv/bin/python -m streamlit run buscador.py
