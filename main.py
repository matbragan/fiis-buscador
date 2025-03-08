import streamlit as st

from data import get_data
from constants import PERCENT_COLS, MONEY_COLS, FLOAT_COLS, INT_COLS

st.set_page_config(page_title='FIIs', layout='wide')

df = get_data(put_plus_data=True)


########################################### SIDEBAR FILTERS
st.sidebar.header('Filtros')


ticker = st.sidebar.text_input('Ticker')
if ticker:
    df = df[df['Ticker'].str.contains(ticker, case=False, na=False)]


tipos_list = df['Tipo'].dropna().unique()
tipos = st.sidebar.multiselect('Tipo(s)', options=tipos_list, default=None)
if tipos:
    df = df[df['Tipo'].isin(tipos)]


segmentos_list = df['Segmento'].dropna().unique()
segmentos = st.sidebar.multiselect('Segmento(s)', options=segmentos_list, default=None)
if segmentos:
    df = df[df['Segmento'].isin(segmentos)]


def numeric_cast(str_value):
    if str_value is None:
        return None
    str_value = str_value.replace('.', '') 
    str_value = str_value.replace(',', '.')
    try:
        return float(str_value)
    except ValueError:
        return None 


p_vp_min_str = st.sidebar.text_input('P/VP Mínimo')
p_vp_max_str = st.sidebar.text_input('P/VP Máximo')

p_vp_min = numeric_cast(p_vp_min_str)
p_vp_max = numeric_cast(p_vp_max_str)

if p_vp_min:
    df = df[df['P/VP'] >= p_vp_min]
if p_vp_max:
    df = df[df['P/VP'] <= p_vp_max]


dy_min_str = st.sidebar.text_input('Dividend Yield Mínimo')
dy_max_str = st.sidebar.text_input('Dividend Yield Máximo')

dy_min = numeric_cast(dy_min_str)
dy_max = numeric_cast(dy_max_str)

if dy_min:
    df = df[df['Dividend Yield'] >= dy_min]
if dy_max:
    df = df[df['Dividend Yield'] <= dy_max]


liquidez_min_str = st.sidebar.text_input('Liquidez Mínima (Mil)')

liquidez_min = numeric_cast(liquidez_min_str)*1000 if liquidez_min_str else None

if liquidez_min:
    df = df[df['Liquidez'] >= liquidez_min]


favorites = st.sidebar.toggle('Favoritos')
if favorites:
    df = df[df['Favorito'] == '⭐']


########################################### MAIN TABLE
st.title(f'{df.shape[0]} FIIs')

df['Ticker'] = df['Ticker'].apply(lambda x: f'<a href="https://investidor10.com.br/fiis/{x.lower()}" target="_blank">{x}</a>')

df = df.drop(columns=df.filter(regex='(approved$|rank$)').columns)
df = df.reset_index(drop=True).reset_index().rename(columns={'index': 'Rank'})
df['Rank'] = df['Rank'] + 1

def format_sufix_money(value):
    if value >= 1_000_000_000:
        formatted = f"R$ {value / 1_000_000_000:.2f} Bilhões"
    elif value >= 1_000_000:
        formatted = f"R$ {value / 1_000_000:.2f} Milhões"
    elif value >= 1_000:
        formatted = f"R$ {value / 1_000:.2f} Mil"
    else:
        formatted = f"R$ {value:.2f}"

    return formatted.replace('.', ',')

formatters = {}
for col in df.columns:
    for col in PERCENT_COLS:
        formatters[col] = lambda x: f'{x:,.2f}%'.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    for col in MONEY_COLS:
        if col == 'Valor de Mercado':
            formatters[col] = lambda x: format_sufix_money(x)
        else:
            formatters[col] = lambda x: f'R$ {x:,.2f}'.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    for col in FLOAT_COLS:
        formatters[col] = lambda x: f'{x:,.2f}'.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    for col in INT_COLS:
        formatters[col] = lambda x: f'{x:,.0f}'.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')


css = '''
<style>
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th {
        background-color: #222831;
        color: white;
        text-align: center !important;
        padding: 10px;
    }
    td {
        text-align: center !important;
        white-space: nowrap;
        padding: 8px;
    }
    tr:nth-child(even) {
        background-color: #393E46;
    }
    tr:nth-child(odd) {
        background-color: #222831;
    }
    a {
        color: #00ADB5;
        text-decoration: none;
    }
</style>
'''

st.markdown(css, unsafe_allow_html=True)
st.markdown(df.to_html(escape=False, index=False, formatters=formatters), unsafe_allow_html=True)
