import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from src.get_fiis import get_data
from src.constants import MY_TICKERS

st.set_page_config(page_title='Meus FIIs - Quantidades', layout='wide')

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    
    .fii-container:hover {
        background-color: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* Estilo para o número input */
    .stNumberInput > div > div > input {
        text-align: center;
        font-weight: bold;
        border-radius: 8px;
    }
    
    /* Espaçamento entre seções */
    .main-container {
        padding: 0.5rem;
    }
    
    /* Melhor espaçamento para as métricas */
    .metric-container {
        margin: 0.5rem 0;
    }
    
    /* Estilo para os botões */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Carrega os dados dos FIIs
df = get_data()
df = df[df['Ticker'].isin(MY_TICKERS)].sort_values('Ticker')

########################################### PERSISTÊNCIA DOS DADOS DE QUANTIDADE

QUANTITY_FILE = 'my_fiis_quantities.json'

def load_quantities():
    """Carrega as quantidades salvas dos FIIs"""
    if os.path.exists(QUANTITY_FILE):
        with open(QUANTITY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_quantities(quantities_dict):
    """Salva as quantidades dos FIIs"""
    with open(QUANTITY_FILE, 'w') as f:
        json.dump(quantities_dict, f)

# Inicializa o estado se não existir
if 'quantities' not in st.session_state:
    st.session_state.quantities = load_quantities()

########################################### INTERFACE PARA INSERIR QUANTIDADES

# Organiza os FIIs em um grid de 2 colunas para economizar espaço
fiis_data = [(row['Ticker'], row['Cotação']) for _, row in df.iterrows()]

# Cria colunas para o grid dos FIIs
fii_col1, fii_col2, fii_col3 = st.columns(3)

# Primeiro, cria todos os widgets
for i, (ticker, cotacao) in enumerate(fiis_data):

    if i % 3 == 0:
        current_col = fii_col1
    elif i % 2 == 0:
        current_col = fii_col3
    else:
        current_col = fii_col2
    
    with current_col:
        # Valor atual salvo ou 0
        current_qty = st.session_state.quantities.get(ticker, 0)
        
        # Container para cada FII com estilo mais compacto
        st.markdown(f'<div class="fii-container">', unsafe_allow_html=True)
        
        # Header do FII
        st.markdown(f"### {ticker}")
        # st.markdown(f"**Cotação:** R$ {cotacao:.2f}")
        
        # Input para quantidade mais compacto
        qty = st.number_input(
            "Quantidade",
            min_value=0,
            value=int(current_qty),
            step=1,
            key=f'qty_{ticker}',
            label_visibility="collapsed"
        )
        
        # Calcula o valor total
        valor_total = qty * cotacao
        st.markdown(f"**💵 Cotação:** R$ {cotacao:.2f}")
        st.markdown(f"**💰 Valor Total:** R$ {valor_total:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'))
        
        # st.markdown('</div>', unsafe_allow_html=True)

# Agora coleta todos os valores dos widgets
edited_quantities = {}
for ticker, _ in fiis_data:
    edited_quantities[ticker] = st.session_state.get(f'qty_{ticker}', 0)

# Botões de ação
btn_col1, btn_col2 = st.columns(2)

with btn_col1:
    if st.button('💾 Salvar', type='primary', use_container_width=True):
        st.session_state.quantities = edited_quantities
        save_quantities(edited_quantities)
        st.success('✅ Salvo com sucesso!')
        st.rerun()

with btn_col2:
    if st.button('🗑️ Limpar', use_container_width=True):
        st.session_state.quantities = {ticker: 0 for ticker in MY_TICKERS.keys()}
        save_quantities(st.session_state.quantities)
        st.success('✅ Limpo com sucesso!')
        st.rerun()

########################################### INFORMAÇÕES ADICIONAIS

atualizado = df['Data Atualização'].min().strftime('%d/%m/%Y %Hh%Mmin')
st.sidebar.text(f'Atualizado {atualizado}')

st.sidebar.header('ℹ️ Informações')
st.sidebar.info(
    "Esta página permite gerenciar as quantidades dos seus FIIs. "
    "Após inserir as quantidades, você pode visualizar a distribuição na página 'Meus FIIs - Distribuição'."
)
