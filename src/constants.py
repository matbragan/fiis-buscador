INVESTIDOR10_BASE_URL = 'https://investidor10.com.br/fiis/'
FUNDAMENTUS_URL = 'https://www.fundamentus.com.br/fii_resultado.php'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
FNET_BASE_URL = 'https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM'

INVESTIDOR10_FILE_NAME = 'investidor10_fiis'
FUNDAMENTUS_FILE_NAME = 'fundamentus_fiis'
COMMUNICATIONS_FILE_NAME = 'communications'
WARD_FILE_NAME = 'ward_fiis'

MY_TICKERS = {
    'NEWL11': '32.527.626/0001-47',
    'BTLG11': '11.839.593/0001-09',
    'TVRI11': '14.410.722/0001-29',
    'RZTR11': '36.501.128/0001-86',
    'RECR11': '28.152.272/0001-26',
    'GGRC11': '26.614.291/0001-00',
    'RZAT11': '28.267.696/0001-36',
    'GARE11': '37.295.919/0001-60',
    'TRXF11': '28.548.288/0001-52',
}

WANTED_TICKERS = {
    'KNCR11': '16.706.958/0001-32',
    'MXRF11': '97.521.225/0001-25',
}

PERCENT_COLS = ['Dividend Yield', 'Vacância', 'Variação 12M', 'Último Yield']
MONEY_COLS = ['Cotação', 'Liquidez Diária', 'Valor de Mercado', 'Valor Patrimonial', 'Último Rendimento']
FLOAT_COLS = ['P/VP']
INT_COLS = ['Rank', 'Qtd de imóveis', 'Número de Cotistas']
