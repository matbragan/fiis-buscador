import json
import os

import pandas as pd
import streamlit as st

from config.settings import MY_FIIS_FILE, WANTED_FIIS_FILE
from src.get_fiis import get_data

st.set_page_config(page_title="Quantidades", layout="wide")

# CSS customizado para melhorar a aparência
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# Carrega os dados dos FIIs
df_all = get_data()

# PERSISTÊNCIA DOS DADOS DE QUANTIDADE


def _get_config_path(filename):
    """Retorna o caminho completo do arquivo de configuração"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(project_root, "config", filename)
    # Garante que o diretório config existe
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    return config_path


def load_quantities():
    """Carrega as quantidades salvas dos FIIs"""
    file_path = _get_config_path(MY_FIIS_FILE)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}


def save_quantities(quantities_dict):
    """Salva as quantidades dos FIIs"""
    file_path = _get_config_path(MY_FIIS_FILE)
    with open(file_path, "w") as f:
        json.dump(quantities_dict, f)


def load_wanted_fiis():
    """Carrega os FIIs desejados salvos"""
    file_path = _get_config_path(WANTED_FIIS_FILE)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}


def save_wanted_fiis(wanted_fiis_dict):
    """Salva os FIIs desejados"""
    file_path = _get_config_path(WANTED_FIIS_FILE)
    with open(file_path, "w") as f:
        json.dump(wanted_fiis_dict, f)


# Inicializa o estado se não existir
if "quantities" not in st.session_state:
    st.session_state.quantities = load_quantities()

    # Não precisa mais inicializar com MY_TICKERS, pois agora tudo vem do arquivo
    save_quantities(st.session_state.quantities)

# Inicializa FIIs desejados
if "wanted_fiis" not in st.session_state:
    st.session_state.wanted_fiis = load_wanted_fiis()
    if st.session_state.wanted_fiis:
        save_wanted_fiis(st.session_state.wanted_fiis)

# Salva o estado anterior para detectar mudanças
if "previous_quantities" not in st.session_state:
    st.session_state.previous_quantities = st.session_state.quantities.copy()

# Flag para controlar reruns automáticos
if "auto_save_flag" not in st.session_state:
    st.session_state.auto_save_flag = False

# SEÇÃO PARA ADICIONAR NOVOS FIIs

st.header("Meus FIIs")

# Busca todos os FIIs disponíveis que não estão cadastrados (não estão no arquivo de quantidades)
all_tickers = sorted(df_all["Ticker"].unique())
available_tickers = [ticker for ticker in all_tickers if ticker not in st.session_state.quantities]

if available_tickers:
    add_col1, add_col2 = st.columns([3, 1])

    with add_col1:
        selected_ticker = st.selectbox(
            "Selecione um FII para adicionar:", options=available_tickers, key="new_fii_select"
        )

    with add_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento
        if st.button("➕ Adicionar FII", type="primary", width="stretch"):
            if selected_ticker:
                # Adiciona o FII ao arquivo de quantidades com quantidade 0
                st.session_state.quantities[selected_ticker] = 0
                save_quantities(st.session_state.quantities)
                st.session_state.previous_quantities = st.session_state.quantities.copy()

                st.success(f"✅ {selected_ticker} adicionado com sucesso!")
                st.rerun()
else:
    st.info("Todos os FIIs disponíveis já foram adicionados.")

# INTERFACE PARA INSERIR QUANTIDADES

st.markdown("<br>", unsafe_allow_html=True)

# Usa os FIIs que estão no arquivo de quantidades (todos os FIIs cadastrados)
all_my_fiis_tickers = set(st.session_state.quantities.keys())

# Filtra o dataframe para incluir todos os FIIs cadastrados
df = df_all[df_all["Ticker"].isin(all_my_fiis_tickers)].sort_values("Ticker")

# Organiza os FIIs em um grid de 2 colunas para economizar espaço
fiis_data = [(row["Ticker"], row["Cotação"]) for _, row in df.iterrows()]

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
        st.markdown('<div class="fii-container">', unsafe_allow_html=True)

        # Header do FII com botão de remover (todos os FIIs podem ser removidos)
        header_col1, header_col2 = st.columns([4, 1])
        with header_col1:
            st.markdown(f"### {ticker}")
        with header_col2:
            # Botão de remover disponível para todos os FIIs
            if st.button("🗑️", key=f"remove_{ticker}", help="Remover FII", width="stretch"):
                # Remove o FII do arquivo de quantidades
                if ticker in st.session_state.quantities:
                    del st.session_state.quantities[ticker]
                    save_quantities(st.session_state.quantities)
                    st.session_state.previous_quantities = st.session_state.quantities.copy()
                st.success(f"✅ {ticker} removido!")
                st.rerun()

        # Input para quantidade mais compacto
        qty = st.number_input(
            "Quantidade",
            min_value=0,
            value=int(current_qty),
            step=1,
            key=f"qty_{ticker}",
            label_visibility="collapsed",
        )

        # Calcula o valor total
        valor_total = qty * cotacao
        st.markdown(f"**💵 Cotação:** R$ {cotacao:.2f}")
        st.markdown(
            f"**💰 Valor Total:** R$ {valor_total:,.2f}".replace(",", "TEMP")
            .replace(".", ",")
            .replace("TEMP", ".")
        )

        # st.markdown('</div>', unsafe_allow_html=True)

# Coleta todos os valores dos widgets
edited_quantities = {}
for ticker, _ in fiis_data:
    edited_quantities[ticker] = st.session_state.get(f"qty_{ticker}", 0)

# Detecta mudanças e salva automaticamente (apenas se não estiver em modo auto-save)
if not st.session_state.auto_save_flag:
    if edited_quantities != st.session_state.previous_quantities:
        st.session_state.quantities = edited_quantities
        save_quantities(edited_quantities)
        st.session_state.previous_quantities = edited_quantities.copy()
        st.session_state.auto_save_flag = True
        st.rerun()
    else:
        # Mantém sincronizado mesmo sem mudanças
        st.session_state.quantities = edited_quantities
else:
    # Reset da flag após o rerun
    st.session_state.auto_save_flag = False
    st.session_state.quantities = edited_quantities
    st.session_state.previous_quantities = edited_quantities.copy()

# SEÇÃO PARA FIIs DESEJADOS

st.markdown("---")
st.header("FIIs Desejados")

# Busca todos os FIIs disponíveis que não estão cadastrados como desejados
all_tickers_wanted = sorted(df_all["Ticker"].unique())
available_tickers_wanted = [
    ticker
    for ticker in all_tickers_wanted
    if ticker not in st.session_state.wanted_fiis and ticker not in st.session_state.quantities
]

if available_tickers_wanted:
    wanted_add_col1, wanted_add_col2 = st.columns([3, 1])

    with wanted_add_col1:
        selected_ticker_wanted = st.selectbox(
            "Selecione um FII para adicionar aos desejados:",
            options=available_tickers_wanted,
            key="new_wanted_fii_select",
        )

    with wanted_add_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento
        if st.button(
            "➕ Adicionar FII Desejado", type="primary", width="stretch", key="add_wanted_fii"
        ):
            if selected_ticker_wanted:
                # Adiciona o FII aos desejados
                st.session_state.wanted_fiis[selected_ticker_wanted] = ""
                save_wanted_fiis(st.session_state.wanted_fiis)

                st.success(f"✅ {selected_ticker_wanted} adicionado aos desejados!")
                st.rerun()
else:
    st.info("Todos os FIIs disponíveis já foram adicionados ou você já possui.")

# Mostra os FIIs desejados cadastrados
if st.session_state.wanted_fiis:
    st.markdown("<br>", unsafe_allow_html=True)

    # Usa os FIIs que estão no arquivo de desejados
    wanted_fiis_tickers = set(st.session_state.wanted_fiis.keys())

    # Filtra o dataframe para incluir todos os FIIs desejados
    df_wanted = df_all[df_all["Ticker"].isin(wanted_fiis_tickers)].sort_values("Ticker")

    if not df_wanted.empty:
        # Organiza os FIIs desejados em um grid
        wanted_fiis_data = [
            (row["Ticker"], row["Cotação"], row.get("P/VP", 0)) for _, row in df_wanted.iterrows()
        ]

        # Cria colunas para o grid dos FIIs desejados
        wanted_col1, wanted_col2, wanted_col3 = st.columns(3)

        for i, (ticker, cotacao, pvp) in enumerate(wanted_fiis_data):
            if i % 3 == 0:
                current_wanted_col = wanted_col1
            elif i % 2 == 0:
                current_wanted_col = wanted_col3
            else:
                current_wanted_col = wanted_col2

            with current_wanted_col:
                st.markdown('<div class="fii-container">', unsafe_allow_html=True)

                # Header do FII com botão de remover
                wanted_header_col1, wanted_header_col2 = st.columns([4, 1])
                with wanted_header_col1:
                    st.markdown(f"### {ticker}")
                with wanted_header_col2:
                    if st.button(
                        "🗑️",
                        key=f"remove_wanted_{ticker}",
                        help="Remover FII desejado",
                        width="stretch",
                    ):
                        if ticker in st.session_state.wanted_fiis:
                            del st.session_state.wanted_fiis[ticker]
                            save_wanted_fiis(st.session_state.wanted_fiis)
                        st.success(f"✅ {ticker} removido dos desejados!")
                        st.rerun()

                # Mostra informações do FII
                st.markdown(f"**💵 Cotação:** R$ {cotacao:.2f}")
                if pd.notna(pvp) and pvp != 0:
                    st.markdown(f"**📊 P/VP:** {pvp:.2f}")
                st.markdown("</div>", unsafe_allow_html=True)

# INFORMAÇÕES ADICIONAIS

if not df.empty:
    atualizado = df["Data Atualização"].min().strftime("%d/%m/%Y %Hh%Mmin")
    st.sidebar.text(f"Atualizado {atualizado}")
else:
    atualizado = df_all["Data Atualização"].min().strftime("%d/%m/%Y %Hh%Mmin")
    st.sidebar.text(f"Atualizado {atualizado}")
