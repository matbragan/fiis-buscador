import os

# Headers & API URLs
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
INVESTIDOR10_BASE_URL = "https://investidor10.com.br/fiis/"
FUNDAMENTUS_URL = "https://www.fundamentus.com.br/fii_resultado.php"
FNET_BASE_URL = "https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM"

# File Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, "downloads")

# Files
INVESTIDOR10_FILE = os.path.join(DOWNLOADS_DIR, "investidor10_fiis.csv")
FUNDAMENTUS_FILE = os.path.join(DOWNLOADS_DIR, "fundamentus_fiis.csv")
COMMUNICATIONS_FILE = os.path.join(DOWNLOADS_DIR, "communications.csv")
WARD_FILE = os.path.join(DOWNLOADS_DIR, "ward_fiis.csv")

MY_FIIS_FILE = os.path.join(CONFIG_DIR, "my_fiis.json")
WANTED_FIIS_FILE = os.path.join(CONFIG_DIR, "wanted_fiis.json")
COMMUNICATIONS_READ_FILE = os.path.join(CONFIG_DIR, "communications_read.json")

# Main Data Columns
PERCENT_COLS = ["Dividend Yield", "Vacância", "Variação 12M", "Último Yield"]
MONEY_COLS = ["Cotação", "Último Rendimento"]
BIG_MONEY_COLS = ["Liquidez Diária", "Valor de Mercado", "Valor Patrimonial"]
FLOAT_COLS = ["P/VP"]
INT_COLS = ["Rank", "Qtd de imóveis", "Número de Cotistas"]
