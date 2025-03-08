URL = 'https://www.fundamentus.com.br/fii_resultado.php'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

PERCENT_COLS = ['Dividend Yield', 'FFO Yield', 'Vacância', 'Variação 12M']
MONEY_COLS = ['Cotação', 'Liquidez', 'Valor de Mercado', 'Último Rendimento'] # , 'Valor Patrimonial'
FLOAT_COLS = ['P/VP']
INT_COLS = ['Rank', 'Qtd de imóveis', 'Número de Cotistas']
