import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import logging
from datetime import datetime
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd

from src.constants import FNET_BASE_URL, MY_TICKERS, WANTED_TICKERS, COMMUNICATIONS_FILE_NAME
from src.utils import write_csv_file


log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


def get_fii_communications(
        ticker: str,
        cnpj: str,
        base_url: str = FNET_BASE_URL,
        attempt: int = 1,
        max_attempts: int = 12
) -> pd.DataFrame:
    '''
    Obtém os 10 últimos comunicados de um FII, no site FNET.

    Args:
        ticker (str): Ticker do FII.
        cnpj (str): CNPJ do FII.
        base_url (str): URL base para fazer a requisição.
        attempt (int): Tentativa atual de obtenção.
        max_attempts (int): Número máximo de tentativas.

    Returns:
        pd.DataFrame: Um DataFrame contendo os comunicados do FII.
    '''
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'--user-data-dir={tempfile.mkdtemp()}')

    driver = webdriver.Chrome(options=options)

    url = base_url + f'?cnpjFundo={cnpj}'
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'tblDocumentosEnviados'))
        )
    except TimeoutException:
        logging.error(f'{ticker} - TimeoutException: {url}')
        raise TimeoutException(f'{ticker} - TimeoutException: {url}')
    except Exception as e:
        logging.error(f'{ticker} - Erro ao obter comunicados: {e}')
        raise Exception(f'{ticker} - Erro ao obter comunicados: {e}')

    rows = driver.find_elements(By.CSS_SELECTOR, '#tblDocumentosEnviados tbody tr')

    data = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        data.append([col.text for col in cols])

    driver.quit()

    columns = [
        'Nome do Fundo', 'Categoria', 'Tipo', 'Espécie',
        'Data de Referência', 'Data de Entrega',
        'Status', 'Versão', 'Modalidade de Envio', 'Ações'
    ]

    df = pd.DataFrame(data, columns=columns)

    if len(df) == 0:
        if attempt < max_attempts:
            logging.info(f'{ticker} - Nenhum comunicado encontrado, tentativa {attempt}/{max_attempts}...')
            return get_fii_communications(ticker, cnpj, base_url, attempt=attempt+1, max_attempts=max_attempts)
        else:
            logging.warning(f'{ticker} - Nenhum comunicado encontrado após {max_attempts} tentativas.')

    df['Ticker'] = ticker
    df['CNPJ'] = cnpj
    df = df[['Ticker', 'CNPJ', 'Categoria', 'Tipo', 'Data de Referência', 'Data de Entrega', 'Status', 'Versão']]

    logging.info(f'{ticker} - {len(df)} comunicados')

    return df


def get_many_fii_communications(
        tickers: dict,
        base_url: str = FNET_BASE_URL
) -> pd.DataFrame:
    '''
    Obtém os 10 últimos comunicados de vários FII, no site FNET.

    Args:
        tickers (dict): Dicionário de tickers dos FII, onde a chave é o ticker e o valor é o CNPJ.
        base_url (str): URL base para fazer a requisição.

    Returns:
        pd.DataFrame: Um DataFrame contendo os comunicados dos FII.
    '''
    logging.info('Leitura de comunicados do site FNET iniciando...')

    dfs = []
    for ticker, cnpj in tickers.items():
        dfs.append(get_fii_communications(ticker, cnpj, base_url))
    df = pd.concat(dfs)

    df['Data Atualização'] = datetime.now()

    logging.info('Todos comunicados obtidos com sucesso!')
    
    return df


if __name__ == '__main__':
    communications = get_many_fii_communications(MY_TICKERS | WANTED_TICKERS)
    
    write_csv_file(data=communications, file_name=COMMUNICATIONS_FILE_NAME)
