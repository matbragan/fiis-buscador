import logging

from config.settings import COMMUNICATIONS_FILE, FUNDAMENTUS_FILE, INVESTIDOR10_FILE, WARD_FILE
from src.scrapes.fnet import main as fnet_main
from src.scrapes.fundamentus import get_fundamentus_data
from src.scrapes.investidor10 import Investidor10Scraper
from src.scrapes.ward import main as ward_main
from src.utils.get_tickers import get_tickers_with_cnpj
from src.utils.write_files import write_csv_file

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

if __name__ == "__main__":
    logging.info("Iniciando scrapes...")

    logging.info("--------------------------------")
    # Investidor10
    FIIsScraper = Investidor10Scraper()
    fiis = FIIsScraper.main()
    write_csv_file(data=fiis, file_path=INVESTIDOR10_FILE)

    logging.info("--------------------------------")
    # Fundamentus
    fiis = get_fundamentus_data()
    write_csv_file(data=fiis, file_path=FUNDAMENTUS_FILE)

    logging.info("--------------------------------")
    # FNET
    communications = fnet_main(get_tickers_with_cnpj())
    write_csv_file(data=communications, file_path=COMMUNICATIONS_FILE)

    logging.info("--------------------------------")
    # Ward
    fiis = ward_main()
    write_csv_file(data=fiis, file_path=WARD_FILE)

    logging.info("--------------------------------")
    logging.info("Todos os scrapes concluídos com sucesso!")
