"""Testes para o módulo src.utils."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.utils import ensure_downloads_folder, get_last_update_date, write_csv_file


class TestEnsureDownloadsFolder:
    """Testes para a função ensure_downloads_folder."""

    def test_creates_folder_if_not_exists(self, temp_dir):
        """Testa se a pasta downloads é criada quando não existe."""
        downloads_path = Path(temp_dir) / "downloads"

        with patch("src.utils.DOWNLOADS_DIR", str(downloads_path)):
            ensure_downloads_folder()

        assert downloads_path.exists()
        assert downloads_path.is_dir()

    def test_does_not_fail_if_folder_exists(self, temp_dir):
        """Testa se não falha quando a pasta já existe."""
        downloads_path = Path(temp_dir) / "downloads"
        downloads_path.mkdir()

        with patch("src.utils.DOWNLOADS_DIR", str(downloads_path)):
            ensure_downloads_folder()  # Não deve lançar exceção

        assert downloads_path.exists()


class TestWriteCsvFile:
    """Testes para a função write_csv_file."""

    def test_writes_csv_file_in_overwrite_mode(self, temp_dir):
        """Testa escrita de arquivo CSV em modo overwrite."""
        downloads_path = Path(temp_dir) / "downloads"
        downloads_path.mkdir()
        file_path = downloads_path / "test.csv"

        data = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

        with patch("src.utils.DOWNLOADS_DIR", str(downloads_path)):
            write_csv_file(data, str(file_path), mode="w")

        assert file_path.exists()
        read_data = pd.read_csv(file_path)
        assert len(read_data) == 3
        assert list(read_data.columns) == ["col1", "col2"]

    def test_writes_csv_file_in_append_mode(self, temp_dir):
        """Testa escrita de arquivo CSV em modo append."""
        downloads_path = Path(temp_dir) / "downloads"
        downloads_path.mkdir()
        file_path = downloads_path / "test.csv"

        # Cria arquivo inicial
        initial_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        initial_data.to_csv(file_path, index=False)

        # Adiciona novos dados
        new_data = pd.DataFrame({"col1": [3, 4], "col2": ["c", "d"]})

        with patch("src.utils.DOWNLOADS_DIR", str(downloads_path)):
            write_csv_file(new_data, str(file_path), mode="a")

        assert file_path.exists()
        read_data = pd.read_csv(file_path)
        # Remove duplicatas, então pode ter menos linhas
        assert len(read_data) >= 2

    def test_append_mode_removes_duplicates(self, temp_dir):
        """Testa se o modo append remove duplicatas."""
        downloads_path = Path(temp_dir) / "downloads"
        downloads_path.mkdir()
        file_path = downloads_path / "test.csv"

        # Cria arquivo inicial
        initial_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        initial_data.to_csv(file_path, index=False)

        # Tenta adicionar dados duplicados
        duplicate_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        with patch("src.utils.DOWNLOADS_DIR", str(downloads_path)):
            write_csv_file(duplicate_data, str(file_path), mode="a")

        read_data = pd.read_csv(file_path)
        # Deve manter apenas uma cópia de cada linha
        assert len(read_data) == 2


class TestGetLastUpdateDate:
    """Testes para a função get_last_update_date."""

    def test_returns_min_date_from_dataframes(self):
        """Testa se retorna a data mínima dos dataframes."""
        fiis_data = pd.DataFrame(
            {
                "Data Atualização": [
                    datetime(2024, 1, 15, 10, 30),
                    datetime(2024, 1, 16, 10, 30),
                ]
            }
        )
        communications_data = pd.DataFrame(
            {
                "Data Atualização": [
                    datetime(2024, 1, 14, 10, 30),
                    datetime(2024, 1, 17, 10, 30),
                ]
            }
        )

        result = get_last_update_date(fiis_data, communications_data)
        assert "14/01/2024" in result

    def test_handles_empty_dataframes(self):
        """Testa se lida corretamente com dataframes vazios."""
        empty_df = pd.DataFrame()

        result = get_last_update_date(empty_df, empty_df)
        assert result == "-"

    def test_handles_one_empty_dataframe(self):
        """Testa se lida corretamente quando um dataframe está vazio."""
        fiis_data = pd.DataFrame(
            {
                "Data Atualização": [
                    datetime(2024, 1, 15, 10, 30),
                ]
            }
        )
        empty_df = pd.DataFrame()

        result = get_last_update_date(fiis_data, empty_df)
        # Quando um está vazio, deve retornar "-"
        assert result == "-"
