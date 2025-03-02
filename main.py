import streamlit as st
import pandas as pd

from data import get_data
from constants import PERCENT_COLS

st.set_page_config(page_title='FIIs', layout='wide')

df = get_data(put_plus_data=True)


########################################### SIDEBAR FILTERS
st.sidebar.header('Filtros')

tipos_list = df['Tipo'].dropna().unique()
tipos = st.sidebar.multiselect('Tipo(s)', options=tipos_list, default=None)
if tipos:
    df = df[df['Tipo'].isin(tipos)]


segmentos_list = df['Segmento'].dropna().unique()
segmentos = st.sidebar.multiselect('Segmento(s)', options=segmentos_list, default=None)
if segmentos:
    df = df[df['Segmento'].isin(segmentos)]


metodo2em1 = st.sidebar.toggle('Método 2 em 1')
if metodo2em1:
    df = df[df['dy_approved'] & df['p_vp_approved'] & df['liquidez_approved'] & df['vacancia_approved']]


ffo_yield_dy = st.sidebar.toggle('FFO Yield > Dividend Yield')
if ffo_yield_dy:
    df = df[df['ffo_yield_approved']]


favorites = st.sidebar.toggle('Favoritos')
if favorites:
    df = df[df['Favorito'] == '⭐']


def numeric_cast(str_value):
    if str_value is None:
        return None
    str_value = str_value.replace('.', '') 
    str_value = str_value.replace(',', '.')
    try:
        return float(str_value)
    except ValueError:
        return None 


dy_min_str = st.sidebar.text_input('Dividend Yield Mínimo')
dy_max_str = st.sidebar.text_input('Dividend Yield Máximo')

dy_min = numeric_cast(dy_min_str)
dy_max = numeric_cast(dy_max_str)

if dy_min:
    df = df[df['Dividend Yield'] >= dy_min]
if dy_max:
    df = df[df['Dividend Yield'] <= dy_max]


p_vp_min_str = st.sidebar.text_input('P/VP Mínimo')
p_vp_max_str = st.sidebar.text_input('P/VP Máximo')

p_vp_min = numeric_cast(p_vp_min_str)
p_vp_max = numeric_cast(p_vp_max_str)

if p_vp_min:
    df = df[df['P/VP'] >= p_vp_min]
if p_vp_max:
    df = df[df['P/VP'] <= p_vp_max]


liquidez_min_str = st.sidebar.text_input('Liquidez Mínima (Mil)')

liquidez_min = numeric_cast(liquidez_min_str)*1000 if liquidez_min_str else None

if liquidez_min:
    df = df[df['Liquidez'] >= liquidez_min]


ticker = st.sidebar.text_input('Ticker')
if ticker:
    df = df[df['Ticker'].str.contains(ticker, case=False, na=False)]


########################################### MAIN TABLE
st.title(f'{df.shape[0]} FIIs')

# df['Ticker'] = df['Ticker'].apply(lambda x: f'<a href="https://www.fundamentus.com.br/detalhes.php?papel={x}" target="_blank">{x}</a>')
# df['Segmento'] = df.apply(lambda row: f'<a href="https://investidor10.com.br/fiis/{row["Ticker"].split(">")[1].split("<")[0].lower()}/" target="_blank">{row["Segmento"]}</a>', axis=1)
df['Ticker'] = df['Ticker'].apply(lambda x: f'<a href="https://investidor10.com.br/fiis/{x.lower()}" target="_blank">{x}</a>')

df = df.drop(columns=df.filter(regex='(approved$|rank$)').columns)
df = df.reset_index(drop=True).reset_index().rename(columns={'index': 'Rank'})
df['Rank'] = df['Rank'] + 1

rename_porcent_cols = {}
for col in PERCENT_COLS:
    rename_porcent_cols[col] = col + ' (%)'

df = df.rename(columns=rename_porcent_cols)

formatters = {}
for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]):
        formatters[col] = lambda x: f'{x:,.2f}'.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    for col in ['Rank', 'Valor de Mercado', 'Liquidez', 'Qtd de imóveis']:
        formatters[col] = lambda x: f'{x:,.0f}'.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')

st.markdown(df.to_html(escape=False, index=False, formatters=formatters), unsafe_allow_html=True)
