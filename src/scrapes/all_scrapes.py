import argparse
import logging

from config.settings import (
    COMMUNICATIONS_FILE,
    FUNDAMENTUS_FILE,
    INVESTIDOR10_DIVIDENDS_FILE,
    INVESTIDOR10_FILE,
    WARD_FILE,
)
from src.scrapes.fnet import main as fnet_main
from src.scrapes.fundamentus import get_fundamentus_data
from src.scrapes.investidor10 import Investidor10Scraper
from src.scrapes.ward import main as ward_main
from src.utils.get_tickers import get_my_tickers, get_tickers_with_cnpj
from src.utils.write_files import write_csv_file

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


def scrape_investidor10_fiis():
    """Scrape dos dados principais dos FIIs do Investidor10."""
    logging.info("--------------------------------")
    logging.info("Iniciando scrape Investidor10 - FIIs...")
    FIIsScraper = Investidor10Scraper()
    fiis = FIIsScraper.main()
    write_csv_file(data=fiis, file_path=INVESTIDOR10_FILE)
    logging.info("✓ Scrape Investidor10 - FIIs concluído!")


def scrape_investidor10_dividends():
    """Scrape dos dividendos dos FIIs do Investidor10."""
    logging.info("--------------------------------")
    logging.info("Iniciando scrape Investidor10 - Dividendos...")
    tickers = list(get_my_tickers())

    if not tickers:
        logging.warning("Nenhum ticker encontrado. Adicione FIIs na página de Quantidades.")
        return

    FIIsScraper = Investidor10Scraper()
    dividends = FIIsScraper.get_all_dividends(tickers=tickers)
    write_csv_file(data=dividends, file_path=INVESTIDOR10_DIVIDENDS_FILE)
    logging.info("✓ Scrape Investidor10 - Dividendos concluído!")


def scrape_fundamentus():
    """Scrape dos dados do Fundamentus."""
    logging.info("--------------------------------")
    logging.info("Iniciando scrape Fundamentus...")
    fiis = get_fundamentus_data()
    write_csv_file(data=fiis, file_path=FUNDAMENTUS_FILE)
    logging.info("✓ Scrape Fundamentus concluído!")


def scrape_fnet():
    """Scrape das comunicações do FNET."""
    logging.info("--------------------------------")
    logging.info("Iniciando scrape FNET...")
    communications = fnet_main(get_tickers_with_cnpj())
    write_csv_file(data=communications, file_path=COMMUNICATIONS_FILE)
    logging.info("✓ Scrape FNET concluído!")


def scrape_ward():
    """Scrape dos dados do Ward."""
    logging.info("--------------------------------")
    logging.info("Iniciando scrape Ward...")
    fiis = ward_main()
    write_csv_file(data=fiis, file_path=WARD_FILE)
    logging.info("✓ Scrape Ward concluído!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa scrapes de dados de FIIs")
    parser.add_argument(
        "--investidor10-fiis",
        action="store_true",
        help="Executa scrape dos dados principais dos FIIs do Investidor10",
    )
    parser.add_argument(
        "--investidor10-dividends",
        action="store_true",
        help="Executa scrape dos dividendos dos FIIs do Investidor10",
    )
    parser.add_argument(
        "--fundamentus",
        action="store_true",
        help="Executa scrape dos dados do Fundamentus",
    )
    parser.add_argument(
        "--fnet",
        action="store_true",
        help="Executa scrape das comunicações do FNET",
    )
    parser.add_argument(
        "--ward",
        action="store_true",
        help="Executa scrape dos dados do Ward",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Executa todos os scrapes",
    )

    args = parser.parse_args()

    # Se nenhum argumento foi passado ou --all foi usado, executa todos
    if args.all or not any(
        [
            args.investidor10_fiis,
            args.investidor10_dividends,
            args.fundamentus,
            args.fnet,
            args.ward,
        ]
    ):
        logging.info("Iniciando todos os scrapes...")
        scrape_investidor10_fiis()
        scrape_investidor10_dividends()
        scrape_fundamentus()
        scrape_fnet()
        scrape_ward()
        logging.info("--------------------------------")
        logging.info("Todos os scrapes concluídos com sucesso!")
    else:
        # Executa apenas os scrapes solicitados
        if args.investidor10_fiis:
            scrape_investidor10_fiis()
        if args.investidor10_dividends:
            scrape_investidor10_dividends()
        if args.fundamentus:
            scrape_fundamentus()
        if args.fnet:
            scrape_fnet()
        if args.ward:
            scrape_ward()
        logging.info("--------------------------------")
        logging.info("Scrapes solicitados concluídos com sucesso!")
