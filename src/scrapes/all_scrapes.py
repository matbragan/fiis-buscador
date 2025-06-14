import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import logging

from src.scrapes.investidor10 import Investidor10Scraper
from src.scrapes.fundamentus import get_fundamentus_data
from src.scrapes.fnet import get_many_fii_communications
from src.utils import write_csv_file
from src.constants import INVESTIDOR10_FILE_NAME, FUNDAMENTUS_FILE_NAME, COMMUNICATIONS_FILE_NAME, FAVORITE_TICKERS

log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)

if __name__ == '__main__':
    logging.info('Iniciando scrapes...')

    # FNET
    communications = get_many_fii_communications(FAVORITE_TICKERS)
    write_csv_file(data=communications, file_name=COMMUNICATIONS_FILE_NAME)

    # Fundamentus
    fiis = get_fundamentus_data()
    write_csv_file(data=fiis, file_name=FUNDAMENTUS_FILE_NAME)

    # Investidor10
    FIIsScraper = Investidor10Scraper()
    fiis = FIIsScraper.get_all_fiis()
    write_csv_file(data=fiis, file_name=INVESTIDOR10_FILE_NAME)

    logging.info('Todos os scrapes concluídos com sucesso!')
