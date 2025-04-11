INVESTIDOR10_BASE_URL = 'https://investidor10.com.br/fiis/'
FUNDAMENTUS_URL = 'https://www.fundamentus.com.br/fii_resultado.php'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

INVESTIDOR10_FILE_NAME = 'investidor10_fiis'
FUNDAMENTUS_FILE_NAME = 'fundamentus_fiis'

PERCENT_COLS = ['Dividend Yield', 'Vacância', 'Variação 12M', 'Último Yield']
MONEY_COLS = ['Cotação', 'Liquidez Diária', 'Valor de Mercado', 'Último Rendimento', 'Valor Patrimonial']
FLOAT_COLS = ['P/VP']
INT_COLS = ['Rank', 'Qtd de imóveis', 'Número de Cotistas']
