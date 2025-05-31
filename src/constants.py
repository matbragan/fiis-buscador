INVESTIDOR10_BASE_URL = 'https://investidor10.com.br/fiis/'
FUNDAMENTUS_URL = 'https://www.fundamentus.com.br/fii_resultado.php'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
FNET_BASE_URL = 'https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM'

INVESTIDOR10_FILE_NAME = 'investidor10_fiis'
FUNDAMENTUS_FILE_NAME = 'fundamentus_fiis'
COMMUNICATIONS_FILE_NAME = 'communications'

FAVORITE_TICKERS = [
    'NEWL11',
    'BTLG11',
    'TVRI11',
    'RZTR11',
    'RECR11',
    'GGRC11',
    'RZAT11',
    'GARE11',
    # 'MXRF11',
]

PERCENT_COLS = ['Dividend Yield', 'Vacância', 'Variação 12M', 'Último Yield']
MONEY_COLS = ['Cotação', 'Liquidez Diária', 'Valor de Mercado', 'Valor Patrimonial', 'Último Rendimento']
FLOAT_COLS = ['P/VP']
INT_COLS = ['Rank', 'Qtd de imóveis', 'Número de Cotistas']
