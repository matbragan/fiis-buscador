import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from src.get_communications import get_data
from src.constants import FNET_BASE_URL, FAVORITE_TICKERS

st.set_page_config(page_title='Comunicados dos FIIs', layout='wide')

df = get_data()
df = df[df['Ticker'].isin(FAVORITE_TICKERS)]

########################################### PERSISTÊNCIA DOS CHECKBOXES

PERSISTENCE_FILE = 'fnet_read.json'

# Função para carregar os dados do JSON
def load_checkbox_state():
    if os.path.exists(PERSISTENCE_FILE):
        with open(PERSISTENCE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Função para salvar os dados no JSON
def save_checkbox_state(state_dict):
    with open(PERSISTENCE_FILE, 'w') as f:
        json.dump(state_dict, f)

# Inicializa o estado se não existir
if 'read' not in st.session_state:
    st.session_state.read = load_checkbox_state()

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

########################################### TABELA INTERATIVA

# Cria um ID único por linha
df['ID'] = df['Ticker'] + '_' + df['Data de Entrega'].astype(str) + '_' + df['Versão'].astype(str)
df['ID'] = df['ID'].str.replace('/', '').str.replace(':', '').str.replace(' ', '')

# Adiciona coluna de seleção com base no session_state
df['Lido'] = df['ID'].map(lambda x: st.session_state.read.get(x, False))

st.title(f"{df['Ticker'].nunique()} FIIs")

unique_tickers = df[['Ticker', 'CNPJ']].drop_duplicates()

# Monta os links no formato HTML
links = [
    f'<a href="{FNET_BASE_URL}?cnpjFundo={row.CNPJ}" target="_blank">{row.Ticker}</a>'
    for _, row in unique_tickers.iterrows()
]

# Junta os links com " | "
link_bar = ' | '.join(links)

# Exibe os links no topo da página
st.markdown(f"##### Documentos - {link_bar}", unsafe_allow_html=True)

# Exibe editor interativo
edited_df = st.data_editor(
    df[['ID', 'Lido', 'Ticker', 'Categoria', 'Tipo', 'Mês de Referência', 'Data de Referência', 'Data de Entrega', 'Status', 'Versão']],
    column_config={
        'Lido': st.column_config.CheckboxColumn(label='Lido'),
        'ID': None,
    },
    hide_index=True,
    use_container_width=True,
)


# Atualiza session_state e salva no JSON
for i, row in edited_df.iterrows():
    st.session_state.read[row['ID']] = row['Lido']

save_checkbox_state(st.session_state.read)

# Conta quantos comunicados não lidos por Ticker
unread_count = (
    df[~df['Lido']]
    .groupby('Ticker')
    .size()
)

if not unread_count.empty:
    st.markdown("### 🔔 Comunicados não lidos por FII")
    for ticker, count in unread_count.items():
        st.markdown(f"- **{ticker}**: {count} comunicado(s) não lido(s)")
else:
    st.markdown("Todos os comunicados foram lidos!")
