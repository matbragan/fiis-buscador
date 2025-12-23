"""
Scraper para obter comunicados dos FIIs do site FNET.
"""

import argparse
import logging
import sys
import tempfile
from datetime import datetime
from time import sleep

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import COMMUNICATIONS_FILE, FNET_BASE_URL
from src.tickers import get_tickers_with_cnpj
from src.utils import write_csv_file

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


def get_unique_fii_communications(
    ticker: str, cnpj: str, base_url: str = FNET_BASE_URL, attempt: int = 1, max_attempts: int = 20
) -> pd.DataFrame:
    """
    Obtém os 10 últimos comunicados de um FII, no site FNET.

    Args:
        ticker (str): Ticker do FII.
        cnpj (str): CNPJ do FII.
        base_url (str): URL base para fazer a requisição.
        attempt (int): Tentativa atual de obtenção.
        max_attempts (int): Número máximo de tentativas.

    Returns:
        pd.DataFrame: Um DataFrame contendo os comunicados do FII.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

    driver = webdriver.Chrome(options=options)

    try:
        cnpj = str(cnpj) if cnpj else ""
        cnpj = cnpj.replace("/", "").replace("-", "").replace(".", "")
        url = base_url + f"?cnpjFundo={cnpj}"
        driver.get(url)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "tblDocumentosEnviados"))
            )
        except TimeoutException:
            logging.error(f"{ticker} - TimeoutException: {url}")
            raise TimeoutException(f"{ticker} - TimeoutException: {url}")
        except Exception as e:
            logging.error(f"{ticker} - Erro ao obter comunicados: {e}")
            raise Exception(f"{ticker} - Erro ao obter comunicados: {e}")

        rows = driver.find_elements(By.CSS_SELECTOR, "#tblDocumentosEnviados tbody tr")

        data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            data.append([col.text for col in cols])
    finally:
        driver.quit()

    if len(data) == 0:
        if attempt < max_attempts:
            if attempt % 5 == 0:
                logging.info(
                    f"{ticker} - Nenhum comunicado encontrado, tentativa {attempt}/{max_attempts}..."
                )
            sleep(0.8)
            return get_unique_fii_communications(ticker, cnpj, base_url, attempt + 1, max_attempts)
        else:
            logging.error(
                f"{ticker} - Nenhum comunicado encontrado após {max_attempts} tentativas."
            )
            return pd.DataFrame()

    columns = [
        "Nome do Fundo",
        "Fundo/Classe",
        "Categoria",
        "Tipo",
        "Espécie",
        "Data de Referência",
        "Data de Entrega",
        "Status",
        "Versão",
        "Modalidade de Envio",
        "Ações",
    ]

    df = pd.DataFrame(data, columns=columns)

    df["Ticker"] = ticker
    df["CNPJ"] = cnpj
    df = df[
        [
            "Ticker",
            "CNPJ",
            "Categoria",
            "Tipo",
            "Data de Referência",
            "Data de Entrega",
            "Status",
            "Versão",
        ]
    ]

    logging.info(f"{ticker} - {len(df)} comunicados")

    return df


def extract_fii_communications(
    tickers: dict, base_url: str = FNET_BASE_URL
) -> tuple[list[pd.DataFrame], list[str]]:
    """
    Extrai os comunicados de vários FIIs, juntando todos os comunicados em um único DataFrame, no site FNET.
    Caso algum FII falhe na obtenção dos comunicados, ele é adicionado à lista de falhas para ser tentado novamente.

    Args:
        tickers (dict): Dicionário de tickers dos FII, onde a chave é o ticker e o valor é o CNPJ.
        base_url (str): URL base para fazer a requisição.

    Returns:
        Retorna um tuple com duas listas:
        - Lista de DataFrames, onde cada DataFrame contém os comunicados de um FII.
        - Lista de tickers que falharam na obtenção dos comunicados.
        Caso algum FII falhe na obtenção dos comunicados, ele é adicionado à lista de falhas para ser tentado novamente.
    """
    dfs = []
    failed_tickers = []

    for ticker, cnpj in tickers.items():
        try:
            df_fii = get_unique_fii_communications(ticker, cnpj, base_url)
            if df_fii.empty or len(df_fii) == 0:
                failed_tickers.append(ticker)
            else:
                dfs.append(df_fii)
        except Exception as e:
            logging.error(f"{ticker} - Falha ao obter comunicados: {e}")
            failed_tickers.append(ticker)

    return dfs, failed_tickers


def main(tickers: dict, base_url: str = FNET_BASE_URL, retry_failed: bool = True) -> pd.DataFrame:
    """
    Obtém os 10 últimos comunicados de vários FII, no site FNET.

    Args:
        tickers (dict): Dicionário de tickers dos FII, onde a chave é o ticker e o valor é o CNPJ.
        base_url (str): URL base para fazer a requisição.
        retry_failed (bool): Se True, tenta novamente os FIIs que falharam na primeira tentativa.

    Returns:
        pd.DataFrame: Um DataFrame contendo os comunicados dos FII.
    """
    logging.info("Leitura de comunicados do site FNET iniciando...")
    logging.info(f"Obtendo comunicados para {len(tickers)} FIIs...")

    dfs, failed_tickers = extract_fii_communications(tickers, base_url)

    if retry_failed and failed_tickers:
        logging.info(
            f"Tentando novamente os {len(failed_tickers)} FIIs que falharam na primeira tentativa: {', '.join(failed_tickers)}"
        )
        sleep(2)

        retry_tickers = {ticker: tickers[ticker] for ticker in failed_tickers}
        retry_dfs, retry_failed_tickers = extract_fii_communications(retry_tickers, base_url)

        dfs.extend(retry_dfs)
        failed_tickers = retry_failed_tickers

    if dfs:
        df = pd.concat(dfs)
        df["Data Atualização"] = datetime.now()

        if failed_tickers:
            logging.warning(
                f'FIIs que não conseguiram obter comunicados após todas as tentativas: {len(failed_tickers)} - {", ".join(failed_tickers)}'
            )
        else:
            logging.info("Todos os comunicados obtidos com sucesso!")
    else:
        logging.warning("Nenhum comunicado foi obtido para nenhum FII!")
        df = pd.DataFrame()

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Obtém comunicados de FIIs do site FNET")
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Lista de tickers para buscar comunicados (opcional). Se não informado, busca todos os tickers cadastrados.",
    )

    args = parser.parse_args()

    all_tickers = get_tickers_with_cnpj()

    if args.tickers:
        filtered_tickers = {
            ticker: cnpj
            for ticker, cnpj in all_tickers.items()
            if ticker.upper() in [t.upper() for t in args.tickers]
        }

        requested_tickers = [t.upper() for t in args.tickers]
        found_tickers = [t.upper() for t in filtered_tickers.keys()]
        missing_tickers = [t for t in requested_tickers if t not in found_tickers]

        if missing_tickers:
            logging.warning(f'Tickers não encontrados: {", ".join(missing_tickers)}')

        if not filtered_tickers:
            logging.error("Nenhum ticker válido foi encontrado!")
            sys.exit(1)

        logging.info(
            f'Buscando comunicados para {len(filtered_tickers)} ticker(s): {", ".join(filtered_tickers.keys())}'
        )
        tickers_to_process = filtered_tickers
        write_mode = "a"
    else:
        tickers_to_process = all_tickers
        write_mode = "w"

    communications = main(tickers_to_process)

    write_csv_file(data=communications, file_path=COMMUNICATIONS_FILE, mode=write_mode)
