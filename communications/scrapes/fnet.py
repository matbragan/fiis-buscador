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
import pandas as pd

from communications.constants import FNET_BASE_URL, TICKERS, COMMUNICATIONS_FILE_NAME


log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


def get_cnpj_by_ticker(
        ticker: str
) -> str:
    df = pd.read_csv('downloads/investidor10_fiis.csv')
    return df[df['Ticker'] == ticker]['CNPJ'].values[0]


def get_fii_communications(
        ticker: str,
        base_url: str = FNET_BASE_URL
) -> pd.DataFrame:
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'--user-data-dir={tempfile.mkdtemp()}')

    driver = webdriver.Chrome(options=options)

    ticker = ticker.upper()
    cnpj = get_cnpj_by_ticker(ticker)
    url = base_url + f'?cnpjFundo={cnpj}'
    driver.get(url)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, 'tblDocumentosEnviados'))
    )

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

    df['Ticker'] = ticker
    df['CNPJ'] = cnpj
    df = df[['Ticker' , 'CNPJ', 'Categoria', 'Tipo', 'Data de Referência', 'Data de Entrega', 'Status', 'Versão']]

    logging.info(f'{ticker} - {len(df)} comunicados')

    return df


def get_many_fii_communications(
        tickers: list,
        base_url: str = FNET_BASE_URL
) -> pd.DataFrame:
    
    dfs = []
    for ticker in tickers:
        dfs.append(get_fii_communications(ticker, base_url))
    df = pd.concat(dfs)

    df['Data Atualização'] = datetime.now()

    logging.info('Todos comunicados obtidos com sucesso!')
    
    return df


if __name__ == '__main__':
    df = get_many_fii_communications(TICKERS)
    df.to_csv(f'downloads/{COMMUNICATIONS_FILE_NAME}.csv', index=False)
