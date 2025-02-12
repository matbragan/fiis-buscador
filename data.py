import requests
import pandas as pd

from constants import URL, HEADERS, PERCENT_COLS
from fiis_segments import fiis_segments
from fiis_favorites import fiis_favorites

def get_data():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        df = pd.read_html(response.content, decimal=',', thousands='.')[0]
    else:
        print(f'Error: {response.status_code}')
        exit(1)

    df['Segmento'] = df['Papel'].map(fiis_segments).fillna(df['Segmento'])
    df['Favorito'] = df['Papel'].apply(lambda x: '⭐' if x in fiis_favorites else '')

    for col in PERCENT_COLS:
        df[col] = df[col].str.replace('%', '').str.replace('.', '', regex=False).str.replace(',', '.').astype(float)

    df['dy_rank'] = df['Dividend Yield'].rank(ascending=False)
    df['p_vp_rank'] = df['P/VP'].rank()
    df['rank'] = df['dy_rank'] + df['p_vp_rank']
    df = df.sort_values(by='rank')

    df['dy_approved'] = df['Dividend Yield'].between(7, 13)
    df['p_vp_approved'] = df['P/VP'].between(0.7, 1.05)
    df['ffo_yield_approved'] = df['FFO Yield'] > df['Dividend Yield']
    df['liquidez_approved'] = df['Liquidez'] >= 400000
    df['vacancia_approved'] = df['Vacância Média'] <= 15

    return df
