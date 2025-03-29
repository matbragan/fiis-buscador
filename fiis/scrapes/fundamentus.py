import os
import sys
import time
import logging

import requests
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from fiis.constants import FUNDAMENTUS_URL, HEADERS, FUNDAMENTUS_FILE_NAME
from fiis.utils import write_csv_file


log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


def get_fundamentus_data(max_retries: int = 20) -> pd.DataFrame:
    ''' 
    Obtém os dados de FIIs do Fundamentus.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs do Fundamentus.
    '''
    retry = 0
    while True:
        response = requests.get(FUNDAMENTUS_URL, headers=HEADERS)
        
        if response.status_code == 200:
            df = pd.read_html(response.content, decimal=',', thousands='.')[0]
            logging.info(f'Tentativa {retry + 1}: Dados obtidos com sucesso!')
            break
        elif response.status_code == 403:
            if retry == max_retries:
                logging.warning(f'Tentativas excedidas {max_retries}: Erro 403, a requisição foi bloqueada pelo site.')
                return
            logging.error(f'Tentativa {retry + 1}: Erro 403, a requisição foi bloqueada pelo site. Tentando novamente...')
            time.sleep(2)
            retry += 1
        else:
            logging.error(f'Erro na requisição: {response.status_code}')
            return

    return df


if __name__ == '__main__':
    fiis = get_fundamentus_data()
    
    write_csv_file(data=fiis, file_name=FUNDAMENTUS_FILE_NAME)
