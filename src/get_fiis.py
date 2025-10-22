from tzlocal import get_localzone
import pandas as pd
import numpy as np

from src.constants import INVESTIDOR10_FILE_NAME, FUNDAMENTUS_FILE_NAME, PERCENT_COLS, MONEY_COLS, FLOAT_COLS, INT_COLS


def join_scrapes() -> pd.DataFrame:
    ''' 
    Junta os dados obtidos dos scrapes dos sites Investidor10 e Fundamentus.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs.
    '''
    investidor10_df = pd.read_csv(f'downloads/{INVESTIDOR10_FILE_NAME}.csv')
    fundamentus_df = pd.read_csv(f'downloads/{FUNDAMENTUS_FILE_NAME}.csv')

    fundamentus_df = fundamentus_df.rename(columns={'Papel': 'Ticker'})
    fundamentus_df = fundamentus_df[['Ticker', 'Qtd de imóveis', 'Valor de Mercado']]

    df = investidor10_df.merge(fundamentus_df, how='left', on='Ticker')

    return df


def get_data() -> pd.DataFrame:
    ''' 
    Obtem os dados de FIIs do site Investidor10 - obtidos através do scrape -
    e adiciona com alguns dados do Fundamentus.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs.
    '''
    df = join_scrapes()

    cols_to_fill = df.columns.difference(PERCENT_COLS + MONEY_COLS + FLOAT_COLS + INT_COLS)
    df[cols_to_fill] = df[cols_to_fill].fillna('')

    df['Último Yield'] = (df['Último Rendimento'] / df['Cotação'] * 100).where(df['Cotação'] != 0, 0)
    
    df['Cálculo Valor de Mercado'] = df['Cotação'] * df['Cotas Emitidas']
    df['Valor de Mercado'] = df['Cálculo Valor de Mercado'].where(df['Cálculo Valor de Mercado'] != 0, df['Valor de Mercado'])
    df['Valor de Mercado'] = df['Valor de Mercado'].astype(float)

    df = df[df['Dados Obtidos'] == True] # Only keep FIIs with data obtained in Investidor10 FII page
    df = df[['Ticker', 'Tipo', 'Segmento', 'Cotação', 'P/VP', 'Dividend Yield', 'Liquidez Diária', 'Qtd de imóveis', 
             'Vacância', 'Variação 12M', 'Tipo de Gestão', 'Último Rendimento', 'Último Yield', 'Valor de Mercado', 
             'Valor Patrimonial', 'Número de Cotistas', 'Público Alvo', 'Taxa de Administração', 'Data Atualização']]

    try:
        ward_fiis = pd.read_csv('downloads/ward_fiis.csv')
        ward_fiis = ward_fiis.rename(columns={'Segmento': 'Segmento2'})
        df = df.merge(ward_fiis, how='left', on='Ticker')
        condition = df['Segmento2'].isnull()
        df['Segmento2'] = np.where(condition, df['Segmento'], df['Segmento2'])
        condition = df['Segmento'].isin(['Outros', 'Híbrido'])
        df['Segmento'] = np.where(condition, df['Segmento2'], df['Segmento'])
        replacements = {
            'Logística': 'Logístico / Indústria / Galpões',
            'Industrial': 'Logístico / Indústria / Galpões',
            'Shoppings': 'Shoppings / Varejo',
            'Varejo': 'Renda Urbana',
            'Papel CRI': 'Títulos e Valores Mobiliários',
            'Outro': 'Outros',
            'Híbrido': 'Outros'
        }
        df['Segmento'] = df['Segmento'].replace(replacements)
        df = df.drop(columns=['Segmento2'])
    except:
        pass

    df['dy_rank'] = df['Dividend Yield'].rank(ascending=False)
    df['p_vp_rank'] = df['P/VP'].rank()
    df['rank'] = df['dy_rank'] + df['p_vp_rank']
    df = df.sort_values(by='rank')

    local_tz = get_localzone()
    df['Data Atualização'] = pd.to_datetime(df['Data Atualização']).dt.tz_localize(local_tz).dt.tz_convert('America/Sao_Paulo')

    return df
