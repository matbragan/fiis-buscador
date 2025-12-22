import os
import sys

import argparse
import logging
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

from src.constants import COMMUNICATIONS_FILE_NAME, FNET_BASE_URL
from src.tickers import get_tickers_with_cnpj
from src.utils import write_csv_file

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


def get_fii_communications(
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
        # Garante que CNPJ seja string antes de processar
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

    if len(df) == 0:
        if attempt < max_attempts:
            if attempt % 5 == 0:
                logging.info(
                    f"{ticker} - Nenhum comunicado encontrado, tentativa {attempt}/{max_attempts}..."
                )
            sleep(0.8)
            return get_fii_communications(
                ticker, cnpj, base_url, attempt=attempt + 1, max_attempts=max_attempts
            )
        else:
            logging.error(
                f"{ticker} - Nenhum comunicado encontrado após {max_attempts} tentativas."
            )
            # Retorna DataFrame vazio quando não consegue obter comunicados
            return pd.DataFrame()

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


def get_many_fii_communications(
    tickers: dict, base_url: str = FNET_BASE_URL, retry_failed: bool = True
) -> pd.DataFrame:
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

    dfs = []
    failed_tickers = []
    logging.info(f"Obtendo comunicados para {len(tickers)} FIIs...")

    for ticker, cnpj in tickers.items():
        try:
            df_fii = get_fii_communications(ticker, cnpj, base_url)
            # Verifica se o DataFrame está vazio (nenhum comunicado encontrado após todas as tentativas)
            if df_fii.empty or len(df_fii) == 0:
                failed_tickers.append(ticker)
            else:
                dfs.append(df_fii)
        except Exception as e:
            logging.error(f"{ticker} - Falha ao obter comunicados: {e}")
            failed_tickers.append(ticker)

    # Retry failed tickers if enabled
    if retry_failed and failed_tickers:
        logging.info(
            f"🔄 Tentando novamente {len(failed_tickers)} FII(s) que falharam na primeira tentativa..."
        )
        sleep(2)  # Pequena pausa antes de tentar novamente

        retry_failed_tickers = []
        retry_tickers_dict = {ticker: tickers[ticker] for ticker in failed_tickers}

        for ticker, cnpj in retry_tickers_dict.items():
            try:
                df_fii = get_fii_communications(ticker, cnpj, base_url)
                if df_fii.empty or len(df_fii) == 0:
                    retry_failed_tickers.append(ticker)
                else:
                    dfs.append(df_fii)
                    logging.info(f"✅ {ticker} - Sucesso na segunda tentativa!")
            except Exception as e:
                logging.error(f"{ticker} - Falha na segunda tentativa: {e}")
                retry_failed_tickers.append(ticker)

        # Atualiza a lista de falhas com os que ainda falharam após retry
        failed_tickers = retry_failed_tickers

    if dfs:
        df = pd.concat(dfs)
        df["Data Atualização"] = datetime.now()

        if failed_tickers:
            logging.info(
                f'⚠️ FIIs que não conseguiram obter comunicados após todas as tentativas ({len(failed_tickers)}): {", ".join(failed_tickers)}'
            )
        else:
            logging.info("✅ Todos os comunicados obtidos com sucesso!")
    else:
        logging.warning("⚠️ Nenhum comunicado foi obtido para nenhum FII!")
        df = pd.DataFrame()
        if failed_tickers:
            logging.info(
                f'❌ FIIs que falharam ({len(failed_tickers)}): {", ".join(failed_tickers)}'
            )

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
        # Filtra apenas os tickers passados como argumento
        filtered_tickers = {
            ticker: cnpj
            for ticker, cnpj in all_tickers.items()
            if ticker.upper() in [t.upper() for t in args.tickers]
        }

        # Verifica se algum ticker não foi encontrado
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
        write_mode = "a"  # Modo append quando tickers são passados como argumento
    else:
        logging.info(f"Buscando comunicados para todos os {len(all_tickers)} ticker(s) cadastrados")
        tickers_to_process = all_tickers
        write_mode = "w"  # Modo overwrite quando nenhum argumento é passado

    communications = get_many_fii_communications(tickers_to_process)

    write_csv_file(data=communications, file_name=COMMUNICATIONS_FILE_NAME, mode=write_mode)
