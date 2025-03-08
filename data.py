import requests
import pandas as pd

from constants import URL, HEADERS, PERCENT_COLS
# from fiis_segments import fiis_segments
from fiis_favorites import fiis_favorites

def get_data(put_plus_data: bool = False):
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        df = pd.read_html(response.content, decimal=',', thousands='.')[0]
    else:
        print(f'Error: {response.status_code}')
        exit(1)

    df = df.drop(columns='Segmento')
    df = df.rename(columns={'Papel': 'Ticker'})
    # df['Segmento'] = df['Ticker'].map(fiis_segments).fillna(df['Segmento'])
    df['Favorito'] = df['Ticker'].apply(lambda x: '⭐' if x in fiis_favorites else '')

    if put_plus_data:
        plus_data = pd.read_csv('downloads/fiis_plus.csv')
        df = df.merge(plus_data, how='inner', on='Ticker')
        df = df[['Ticker', 'Tipo', 'Segmento', 'Cotação_y', 'P/VP_y', 'Dividend Yield_y', 'FFO Yield', 'Liquidez_y', 
                 'Qtd de imóveis', 'Vacância', 'Variação 12M', 'Tipo de Gestão', 'Público Alvo', 'Valor de Mercado', 
                 'Valor Patrimonial', 'Número de Cotistas', 'Último Rendimento', 'Taxa de Administração', 'Favorito']]
        df = df.rename(columns={'Cotação_y': 'Cotação', 'P/VP_y': 'P/VP', 
                                'Dividend Yield_y': 'Dividend Yield', 'Liquidez_y': 'Liquidez'})
    else:
        tipo_segmento = pd.read_csv('downloads/fiis.csv')
        df = df.merge(tipo_segmento[['Ticker', 'Tipo', 'Segmento']], how='inner', on='Ticker')
        df = df[['Ticker', 'Tipo', 'Segmento', 'Cotação', 'P/VP', 'Dividend Yield', 'FFO Yield', 
                 'Liquidez', 'Qtd de imóveis', 'Vacância Média', 'Valor de Mercado', 'Favorito']]
        df = df.rename(columns={'Vacância Média': 'Vacância'})

    for col in PERCENT_COLS:
        if col != 'Variação 12M':
            df[col] = df[col].str.replace('%', '').str.replace('.', '', regex=False).str.replace(',', '.').astype(float)

    df['Tipo'] = df['Tipo'].replace({
        'Fundo de tijolo': 'Fundo de Tijolo',
        'Fundo de papel': 'Fundo de Papel',
        'Fundo de desenvolvimento': 'Fundo de Desenvolvimento',
        'Fundo de fundos': 'Fundo de Fundos',
        'Fundo misto': 'Fundo Misto'
    })
    

    df['Público Alvo'] = df['Público Alvo'].replace({
        'fii.QUALIFIED_INVESTOR': 'Investidor Qualificado',
        'fii.GENERAL': 'Geral'
    })

    df['Tipo de Gestão'] = df['Tipo de Gestão'].replace({
        'Passive': 'Passiva',
        'Active': 'Ativa'
    })


    df['dy_rank'] = df['Dividend Yield'].rank(ascending=False)
    df['p_vp_rank'] = df['P/VP'].rank()
    df['rank'] = df['dy_rank'] + df['p_vp_rank']
    df = df.sort_values(by='rank')

    return df
