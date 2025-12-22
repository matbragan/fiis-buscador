import logging
import os

import pandas as pd

from config.settings import DOWNLOADS_DIR

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


def ensure_downloads_folder() -> None:
    """Cria a pasta 'downloads' um nível acima do diretório do script, se não existir."""
    downloads_path = DOWNLOADS_DIR

    if not os.path.exists(downloads_path):
        os.makedirs(downloads_path)
        logging.info(f'Pasta "downloads" criada em: {downloads_path}')


def write_csv_file(data: pd.DataFrame, file_path: str, mode: str = "w") -> None:
    """
    Escreve um arquivo CSV com os dados fornecidos, escrita feita na pasta downloads.

    Args:
        data (pd.DataFrame): DataFrame contendo os dados.
        file_path (str): Caminho completo do arquivo CSV.
        mode (str): Modo de escrita - 'w' para overwrite (padrão) ou 'a' para append.
    """
    ensure_downloads_folder()

    if mode == "a" and os.path.exists(file_path):
        # Modo append: lê o arquivo existente e concatena com os novos dados
        existing_data = pd.read_csv(file_path)
        # Remove duplicatas baseado em todas as colunas (exceto 'Data Atualização' se existir)
        combined_data = pd.concat([existing_data, data], ignore_index=True)
        # Remove duplicatas completas mantendo a última ocorrência
        combined_data = combined_data.drop_duplicates(keep="last")
        combined_data.to_csv(file_path, index=False)
        logging.info(f"Arquivo {file_path} atualizado (append) com sucesso!")
    else:
        # Modo overwrite: escreve o arquivo normalmente
        data.to_csv(file_path, index=False)
        logging.info(f"Arquivo {file_path} escrito com sucesso!")
