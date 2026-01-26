"""Testes para o módulo src.tickers."""

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.tickers import (
    get_my_tickers,
    get_my_tickers_dict,
    get_tickers_with_cnpj,
    get_wanted_tickers,
    get_wanted_tickers_dict,
)


class TestGetMyTickers:
    """Testes para a função get_my_tickers."""

    def test_returns_set_of_tickers_from_json(self, temp_dir):
        """Testa se retorna um set com os tickers do arquivo JSON."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        json_file = config_dir / "my_fiis.json"

        data = {"HGLG11": {"quantidade": 100}, "XPLG11": {"quantidade": 50}}
        json_file.write_text(json.dumps(data))

        with patch("src.tickers.MY_FIIS_FILE", str(json_file)):
            result = get_my_tickers()

        assert isinstance(result, set)
        assert "HGLG11" in result
        assert "XPLG11" in result
        assert len(result) == 2

    def test_returns_empty_set_when_file_not_exists(self, temp_dir):
        """Testa se retorna set vazio quando arquivo não existe."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        json_file = config_dir / "nonexistent.json"

        with patch("src.tickers.MY_FIIS_FILE", str(json_file)):
            result = get_my_tickers()

        assert isinstance(result, set)
        assert len(result) == 0


class TestGetWantedTickers:
    """Testes para a função get_wanted_tickers."""

    def test_returns_set_of_tickers_from_json(self, temp_dir):
        """Testa se retorna um set com os tickers desejados do arquivo JSON."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        json_file = config_dir / "wanted_fiis.json"

        data = {"VISC11": {}, "HGLG11": {}}
        json_file.write_text(json.dumps(data))

        with patch("src.tickers.WANTED_FIIS_FILE", str(json_file)):
            result = get_wanted_tickers()

        assert isinstance(result, set)
        assert "VISC11" in result
        assert "HGLG11" in result
        assert len(result) == 2

    def test_returns_empty_set_when_file_not_exists(self, temp_dir):
        """Testa se retorna set vazio quando arquivo não existe."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        json_file = config_dir / "nonexistent.json"

        with patch("src.tickers.WANTED_FIIS_FILE", str(json_file)):
            result = get_wanted_tickers()

        assert isinstance(result, set)
        assert len(result) == 0


class TestGetMyTickersDict:
    """Testes para a função get_my_tickers_dict."""

    def test_returns_dict_with_tickers(self, temp_dir):
        """Testa se retorna um dicionário com os tickers."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        json_file = config_dir / "my_fiis.json"

        data = {"HGLG11": {"quantidade": 100}, "XPLG11": {"quantidade": 50}}
        json_file.write_text(json.dumps(data))

        with patch("src.tickers.MY_FIIS_FILE", str(json_file)):
            result = get_my_tickers_dict()

        assert isinstance(result, dict)
        assert "HGLG11" in result
        assert "XPLG11" in result
        assert result["HGLG11"] == ""
        assert result["XPLG11"] == ""

    def test_returns_empty_dict_when_file_not_exists(self, temp_dir):
        """Testa se retorna dict vazio quando arquivo não existe."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        json_file = config_dir / "nonexistent.json"

        with patch("src.tickers.MY_FIIS_FILE", str(json_file)):
            result = get_my_tickers_dict()

        assert isinstance(result, dict)
        assert len(result) == 0


class TestGetWantedTickersDict:
    """Testes para a função get_wanted_tickers_dict."""

    def test_returns_dict_with_wanted_tickers(self, temp_dir):
        """Testa se retorna um dicionário com os tickers desejados."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        json_file = config_dir / "wanted_fiis.json"

        data = {"VISC11": {}, "HGLG11": {}}
        json_file.write_text(json.dumps(data))

        with patch("src.tickers.WANTED_FIIS_FILE", str(json_file)):
            result = get_wanted_tickers_dict()

        assert isinstance(result, dict)
        assert "VISC11" in result
        assert "HGLG11" in result

    def test_returns_empty_dict_when_file_not_exists(self, temp_dir):
        """Testa se retorna dict vazio quando arquivo não existe."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        json_file = config_dir / "nonexistent.json"

        with patch("src.tickers.WANTED_FIIS_FILE", str(json_file)):
            result = get_wanted_tickers_dict()

        assert isinstance(result, dict)
        assert len(result) == 0


class TestGetTickersWithCnpj:
    """Testes para a função get_tickers_with_cnpj."""

    def test_returns_dict_with_tickers_and_cnpj(self, temp_dir):
        """Testa se retorna dicionário com tickers e CNPJs."""
        config_dir = Path(temp_dir) / "config"
        downloads_dir = Path(temp_dir) / "downloads"
        config_dir.mkdir()
        downloads_dir.mkdir()

        # Cria arquivo CSV com CNPJs
        csv_file = downloads_dir / "investidor10_fiis.csv"
        csv_data = pd.DataFrame(
            {
                "Ticker": ["HGLG11", "XPLG11", "VISC11"],
                "CNPJ": ["12345678000190", "98765432000110", "11111111000111"],
            }
        )
        csv_data.to_csv(csv_file, index=False)

        # Cria arquivo JSON com meus FIIs
        json_file = config_dir / "my_fiis.json"
        json_data = {"HGLG11": {"quantidade": 100}}
        json_file.write_text(json.dumps(json_data))

        with patch("src.tickers.INVESTIDOR10_FILE", str(csv_file)):
            with patch("src.tickers.MY_FIIS_FILE", str(json_file)):
                result = get_tickers_with_cnpj()

        assert isinstance(result, dict)
        assert "HGLG11" in result
        assert result["HGLG11"] == "12345678000190"

    def test_handles_missing_cnpj_gracefully(self, temp_dir):
        """Testa se lida graciosamente com CNPJs ausentes."""
        config_dir = Path(temp_dir) / "config"
        downloads_dir = Path(temp_dir) / "downloads"
        config_dir.mkdir()
        downloads_dir.mkdir()

        # Cria arquivo CSV sem o ticker
        csv_file = downloads_dir / "investidor10_fiis.csv"
        csv_data = pd.DataFrame(
            {
                "Ticker": ["XPLG11"],
                "CNPJ": ["98765432000110"],
            }
        )
        csv_data.to_csv(csv_file, index=False)

        # Cria arquivo JSON com ticker que não está no CSV
        json_file = config_dir / "my_fiis.json"
        json_data = {"HGLG11": {"quantidade": 100}}
        json_file.write_text(json.dumps(json_data))

        with patch("src.tickers.INVESTIDOR10_FILE", str(csv_file)):
            with patch("src.tickers.MY_FIIS_FILE", str(json_file)):
                result = get_tickers_with_cnpj()

        assert isinstance(result, dict)
        assert "HGLG11" in result
        assert result["HGLG11"] == ""  # CNPJ vazio quando não encontrado

    def test_returns_empty_dict_when_csv_not_exists(self, temp_dir):
        """Testa se retorna dict vazio quando CSV não existe."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()

        json_file = config_dir / "my_fiis.json"
        json_data = {"HGLG11": {"quantidade": 100}}
        json_file.write_text(json.dumps(json_data))

        nonexistent_csv = Path(temp_dir) / "nonexistent.csv"

        with patch("src.tickers.INVESTIDOR10_FILE", str(nonexistent_csv)):
            with patch("src.tickers.MY_FIIS_FILE", str(json_file)):
                result = get_tickers_with_cnpj()

        assert isinstance(result, dict)
        assert len(result) == 0
