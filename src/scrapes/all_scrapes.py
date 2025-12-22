import logging

from config.settings import COMMUNICATIONS_FILE, FUNDAMENTUS_FILE, INVESTIDOR10_FILE, WARD_FILE
from src.scrapes.fnet import get_many_fii_communications
from src.scrapes.fundamentus import get_fundamentus_data
from src.scrapes.investidor10 import Investidor10Scraper
from src.scrapes.ward import get_ward_fiis
from src.tickers import get_tickers_with_cnpj
from src.utils import write_csv_file

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

if __name__ == "__main__":
    logging.info("Iniciando scrapes...")

    logging.info("--------------------------------")
    # Investidor10
    FIIsScraper = Investidor10Scraper()
    fiis = FIIsScraper.get_all_fiis()
    write_csv_file(data=fiis, file_path=INVESTIDOR10_FILE)

    logging.info("--------------------------------")
    # Fundamentus
    fiis = get_fundamentus_data()
    write_csv_file(data=fiis, file_path=FUNDAMENTUS_FILE)

    logging.info("--------------------------------")
    # FNET
    communications = get_many_fii_communications(get_tickers_with_cnpj())
    write_csv_file(data=communications, file_path=COMMUNICATIONS_FILE)

    logging.info("--------------------------------")
    # Ward
    fiis = get_ward_fiis()
    write_csv_file(data=fiis, file_path=WARD_FILE)

    logging.info("--------------------------------")
    logging.info("Todos os scrapes concluídos com sucesso!")
