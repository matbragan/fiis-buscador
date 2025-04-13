import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

from communications.get_communications import get_data
from communications.constants import FNET_BASE_URL

st.set_page_config(page_title='Comunicados dos FIIs', layout='wide')

df = get_data()


########################################### SIDEBAR FILTERS
atualizado = df['Data Atualização'].min().strftime('%d/%m/%Y %Hh%Mmin')
st.sidebar.text(f'Atualizado {atualizado}')


st.sidebar.header('Filtros')


tickers_list = sorted(df['Ticker'].dropna().unique())
tickers = st.sidebar.multiselect('Ticker(s)', options=tickers_list, default=None)
if tickers:
    df = df[df['Ticker'].isin(tickers)]


category_list = sorted(df['Categoria'].dropna().unique())
category = st.sidebar.multiselect('Categoria(s)', options=category_list, default=None)
if category:
    df = df[df['Categoria'].isin(category)]


type_list = sorted(df['Tipo'].dropna().unique())
type = st.sidebar.multiselect('Tipo(s)', options=type_list, default=None)
if type:
    df = df[df['Tipo'].isin(type)]


########################################### MAIN TABLE
st.title(f'{df.nunique()["Ticker"]} FIIs')

df['Ticker'] = df.apply(lambda row: f'<a href="{FNET_BASE_URL}?cnpjFundo={row["CNPJ"]}" target="_blank">{row["Ticker"]}</a>', axis=1)


df = df.drop(columns=['CNPJ', 'Data Atualização'])


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
        height: 100px;
        font-size: 16px;
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
st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
