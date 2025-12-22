import os
import logging
import pandas as pd


log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


def get_downloads_path() -> str:
    """Retorna o caminho da pasta downloads, um nível acima do diretório do script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    return os.path.join(parent_dir, "downloads")


def ensure_downloads_folder() -> None:
    """Cria a pasta 'downloads' um nível acima do diretório do script, se não existir."""
    downloads_path = get_downloads_path()

    if not os.path.exists(downloads_path):
        os.makedirs(downloads_path)
        logging.info(f'Pasta "downloads" criada em: {downloads_path}')


def write_csv_file(data: pd.DataFrame, file_name: str, mode: str = "w") -> None:
    """
    Escreve um arquivo CSV com os dados fornecidos, escrita feita na pasta downloads.

    Args:
        data (pd.DataFrame): DataFrame contendo os dados.
        file_name (str): Nome do arquivo CSV.
        mode (str): Modo de escrita - 'w' para overwrite (padrão) ou 'a' para append.
    """
    ensure_downloads_folder()
    downloads_path = get_downloads_path()
    file_path = f"{downloads_path}/{file_name}.csv"

    if mode == "a" and os.path.exists(file_path):
        # Modo append: lê o arquivo existente e concatena com os novos dados
        existing_data = pd.read_csv(file_path)
        # Remove duplicatas baseado em todas as colunas (exceto 'Data Atualização' se existir)
        combined_data = pd.concat([existing_data, data], ignore_index=True)
        # Remove duplicatas completas mantendo a última ocorrência
        combined_data = combined_data.drop_duplicates(keep="last")
        combined_data.to_csv(file_path, index=False)
        logging.info(f"Arquivo {file_name}.csv atualizado (append) com sucesso!")
    else:
        # Modo overwrite: escreve o arquivo normalmente
        data.to_csv(file_path, index=False)
        logging.info(f"Arquivo {file_name}.csv escrito com sucesso!")
