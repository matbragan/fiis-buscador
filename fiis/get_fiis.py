import os
import sys

import requests
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fiis.constants import FUNDAMENTUS_URL, HEADERS, FILE_NAME


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
        print(f'Erro na requisição do Fundamentus: {response.status_code}')
        return

    return df


def get_data() -> pd.DataFrame:
    ''' 
    Obtem os dados de FIIs do site Investidor10 - obtidos através do scrape -
    e adiciona com alguns dados do Fundamentus.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs.
    '''
    df = pd.read_csv(f'downloads/{FILE_NAME}.csv')
    
    fundamentus_df = get_fundamentus_data()
    fundamentus_df = fundamentus_df.rename(columns={'Papel': 'Ticker'})
    fundamentus_df = fundamentus_df[['Ticker', 'Qtd de imóveis', 'Valor de Mercado']]

    df = df.merge(fundamentus_df, how='left', on='Ticker')
    df = df[['Ticker', 'Tipo', 'Segmento', 'Cotação', 'P/VP', 'Dividend Yield', 'Liquidez Diária',
             'Qtd de imóveis', 'Vacância', 'Variação 12M', 'Tipo de Gestão', 'Público Alvo', 'Valor de Mercado',
             'Valor Patrimonial', 'Número de Cotistas', 'Último Rendimento', 'Taxa de Administração', 'Data Atualização']]

    df['dy_rank'] = df['Dividend Yield'].rank(ascending=False)
    df['p_vp_rank'] = df['P/VP'].rank()
    df['rank'] = df['dy_rank'] + df['p_vp_rank']
    df = df.sort_values(by='rank')

    df['Data Atualização'] = pd.to_datetime(df['Data Atualização'])

    return df


if __name__ == '__main__':
    df = get_fundamentus_data()
