import logging
import requests
import pandas as pd

from fiis.constants import FUNDAMENTUS_URL, HEADERS
from fiis.utils import write_csv_file


log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


def get_fundamentus_data() -> pd.DataFrame:
    ''' 
    Obtém os dados de FIIs do Fundamentus.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs do Fundamentus.
    '''
    response = requests.get(FUNDAMENTUS_URL, headers=HEADERS)
    
    if response.status_code == 200:
        df = pd.read_html(response.content, decimal=',', thousands='.')[0]
    else:
        logging.error(f'Erro na requisição: {response.status_code}')
        exit(1)

    return df


if __name__ == '__main__':
    fiis = get_fundamentus_data()
    
    write_csv_file(data=fiis, file_name='fundamentus_fiis.csv')
