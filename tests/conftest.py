"""Configurações compartilhadas para os testes."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Cria um diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_csv_data():
    """Retorna dados CSV de exemplo para testes."""
    from datetime import datetime

    import pandas as pd

    return pd.DataFrame(
        {
            "Ticker": ["HGLG11", "XPLG11", "VISC11"],
            "CNPJ": ["12345678000190", "98765432000110", "11111111000111"],
            "Data Atualização": [
                datetime(2024, 1, 15, 10, 30),
                datetime(2024, 1, 15, 10, 30),
                datetime(2024, 1, 15, 10, 30),
            ],
        }
    )


@pytest.fixture
def sample_json_data():
    """Retorna dados JSON de exemplo para testes."""
    return {
        "HGLG11": {"quantidade": 100},
        "XPLG11": {"quantidade": 50},
    }


@pytest.fixture
def mock_config_dir(temp_dir):
    """Cria um diretório de configuração temporário."""
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_downloads_dir(temp_dir):
    """Cria um diretório de downloads temporário."""
    downloads_dir = Path(temp_dir) / "downloads"
    downloads_dir.mkdir()
    return downloads_dir
