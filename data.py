import requests
import pandas as pd

from constants import URL, HEADERS, PERCENT_COLS

def get_data():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        df = pd.read_html(response.content, decimal=',', thousands='.')[0]
    else:
        print(f'Error: {response.status_code}')
        exit(1)

    for col in PERCENT_COLS:
        df[col] = df[col].str.replace('%', '').str.replace('.', '', regex=False).str.replace(',', '.').astype(float)

    df['dy_rank'] = df['Dividend Yield'].rank(ascending=False)
    df['p_vp_rank'] = df['P/VP'].rank()
    df['rank'] = df['dy_rank'] + df['p_vp_rank']
    df = df.sort_values(by='rank')

    df['dy_approved'] = df['Dividend Yield'].between(7, 13)
    df['p_vp_approved'] = df['P/VP'].between(0.7, 1.05)
    df['ffo_yield_approved'] = df['FFO Yield'] > df['Dividend Yield']
    df['liquidez_approved'] = df['Liquidez'] >= 300000

    df['Papel'] = df['Papel'].apply(lambda x: f'<a href="https://www.fundamentus.com.br/detalhes.php?papel={x}" target="_blank">{x}</a>')
    df['Segmento'] = df.apply(lambda row: f'<a href="https://investidor10.com.br/fiis/{row["Papel"].split(">")[1].split("<")[0].lower()}/" target="_blank">{row["Segmento"]}</a>', axis=1)

    return df
