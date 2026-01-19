"""
Scraper para obter dados dos FIIs do site Fundamentus.
"""

import logging
import time

import pandas as pd
import requests

from config.settings import FUNDAMENTUS_FILE, FUNDAMENTUS_URL, HEADERS
from src.utils.write_files import write_csv_file

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


def get_fundamentus_data(max_attempts: int = 20) -> pd.DataFrame:
    """
    Obtém os dados de FIIs do Fundamentus.

    Args:
        max_attempts (int): Número de tentativas de obtenção dos dados.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs do Fundamentus.
    """
    logging.info("Leitura de dados do site Fundamentus iniciando...")

    attempt = 1
    while True:
        response = requests.get(FUNDAMENTUS_URL, headers=HEADERS)

        if response.status_code == 200:
            df = pd.read_html(response.content, decimal=",", thousands=".")[0]
            logging.info(f"Tentativa {attempt}: Dados obtidos com sucesso!")
            break
        elif response.status_code == 403:
            if attempt == max_attempts:
                logging.warning(
                    f"Tentativas excedidas {attempt}: Erro 403, a requisição foi bloqueada pelo site."
                )
                return
            logging.error(
                f"Tentativa {attempt}: Erro 403, a requisição foi bloqueada pelo site. Tentando novamente..."
            )
            time.sleep(2)
            attempt += 1
        else:
            logging.error(f"Erro na requisição: {response.status_code}")
            return

    logging.info("✓ Leitura de dados do site Fundamentus concluida!")
    return df


if __name__ == "__main__":
    fiis = get_fundamentus_data()

    write_csv_file(data=fiis, file_path=FUNDAMENTUS_FILE)
