import json
import os
import sys

import streamlit as st

from src.constants import FNET_BASE_URL
from src.get_communications import get_data
from src.tickers import get_my_tickers, get_wanted_tickers

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="Comunicados", layout="wide")

df = get_data()
df = df[df["Ticker"].isin(get_my_tickers() | get_wanted_tickers())]

"""
------------------------------------------
PERSISTÊNCIA DOS CHECKBOXES
------------------------------------------
"""

PERSISTENCE_FILE = "fnet_read.json"


# Função para carregar os dados do JSON
def load_checkbox_state():
    if os.path.exists(PERSISTENCE_FILE):
        with open(PERSISTENCE_FILE, "r") as f:
            return json.load(f)
    return {}


# Função para salvar os dados no JSON
def save_checkbox_state(state_dict):
    with open(PERSISTENCE_FILE, "w") as f:
        json.dump(state_dict, f)


# Inicializa o estado se não existir
if "read" not in st.session_state:
    st.session_state.read = load_checkbox_state()

"""
------------------------------------------
SIDEBAR FILTERS
------------------------------------------
"""
atualizado = df["Data Atualização"].min().strftime("%d/%m/%Y %Hh%Mmin")
st.sidebar.text(f"Atualizado {atualizado}")

st.sidebar.header("Filtros")

tickers_list = sorted(df["Ticker"].dropna().unique())
tickers = st.sidebar.multiselect("Ticker(s)", options=tickers_list, default=None)
if tickers:
    df = df[df["Ticker"].isin(tickers)]

category_list = sorted(df["Categoria"].dropna().unique())
category = st.sidebar.multiselect("Categoria(s)", options=category_list, default=None)
if category:
    df = df[df["Categoria"].isin(category)]

type_list = sorted(df["Tipo"].dropna().unique())
type = st.sidebar.multiselect("Tipo(s)", options=type_list, default=None)
if type:
    df = df[df["Tipo"].isin(type)]


st.sidebar.divider()


my_tickers = st.sidebar.toggle("Meus FIIs", value=True)
if my_tickers:
    df = df[df["Ticker"].isin(get_my_tickers())]

wanted_tickers = st.sidebar.toggle("FIIs Desejados")
if wanted_tickers:
    df = df[df["Ticker"].isin(get_wanted_tickers())]

"""
------------------------------------------
TABELA INTERATIVA
------------------------------------------
"""

# Cria um ID único por linha
df["ID"] = df["Ticker"] + "_" + df["Data de Entrega"].astype(str) + "_" + df["Versão"].astype(str)
df["ID"] = df["ID"].str.replace("/", "").str.replace(":", "").str.replace(" ", "")

# Adiciona coluna de seleção com base no session_state
df["Lido"] = df["ID"].map(lambda x: st.session_state.read.get(x, False))

# Formata a coluna Status para adicionar emoji quando for Inativo ou Cancelado
df["Status_Formatado"] = df["Status"].apply(
    lambda x: f"❌ {x}" if str(x).strip() in ["Inativo", "Cancelado"] else str(x)
)

# Formata a coluna Categoria para adicionar emoji quando o status for Inativo ou Cancelado
df["Categoria_Formatada"] = df.apply(
    lambda row: (
        f"❌ {row['Categoria']}"
        if str(row["Status"]).strip() in ["Inativo", "Cancelado"]
        else str(row["Categoria"])
    ),
    axis=1,
)

st.title(f"{df['Ticker'].nunique()} FIIs")

unique_tickers = df[["Ticker", "CNPJ"]].drop_duplicates()

# Monta os links no formato HTML
links = [
    f'<a href="{FNET_BASE_URL}?cnpjFundo={row.CNPJ}" target="_blank">{row.Ticker}</a>'
    for _, row in unique_tickers.iterrows()
]

# Junta os links com " | "
link_bar = " | ".join(links)

# Exibe os links no topo da página
st.markdown(f"##### Documentos - {link_bar}", unsafe_allow_html=True)

# Salva o estado anterior para detectar mudanças
if "previous_read_state" not in st.session_state:
    st.session_state.previous_read_state = st.session_state.read.copy()

previous_state = st.session_state.previous_read_state.copy()

# Exibe editor interativo
edited_df = st.data_editor(
    df[
        [
            "ID",
            "Lido",
            "Ticker",
            "Categoria_Formatada",
            "Tipo",
            "Mês de Referência",
            "Data de Entrega",
            "Status_Formatado",
            "Versão",
        ]
    ],
    column_config={
        "Lido": st.column_config.CheckboxColumn(label="Lido"),
        "ID": None,
        "Categoria_Formatada": st.column_config.TextColumn(label="Categoria"),
        "Status_Formatado": st.column_config.TextColumn(label="Status"),
    },
    hide_index=True,
    width="stretch",
)


# Atualiza session_state e salva no JSON
for i, row in edited_df.iterrows():
    st.session_state.read[row["ID"]] = row["Lido"]

save_checkbox_state(st.session_state.read)

# Detecta se houve mudanças e faz rerun automático
if previous_state != st.session_state.read:
    st.session_state.previous_read_state = st.session_state.read.copy()
    st.rerun()

# Conta quantos comunicados não lidos por Ticker
unread_count = df[~df["Lido"]].groupby("Ticker").size().sort_index()

# Conta todos os FIIs (incluindo os que têm todos os comunicados lidos)
all_tickers_count = df.groupby("Ticker").size().sort_index()

# Preenche com 0 os FIIs que não têm comunicados não lidos
unread_count = unread_count.reindex(all_tickers_count.index, fill_value=0)

# Calcula total de comunicados não lidos
total_unread = unread_count.sum() if not unread_count.empty else 0

# Seção de comunicados não lidos
# st.divider()

if not unread_count.empty:
    # CSS para ajustar cores no dark mode do Streamlit
    st.markdown(
        """
    <style>
        .fii-card-text {
            color: #333;
        }
        .fii-card-subtext {
            color: #666;
        }
        /* Detecta dark mode usando seletores do Streamlit */
        [data-baseweb="base-dark"] ~ * .fii-card-text,
        [data-baseweb="base-dark"] .fii-card-text,
        section:has([data-baseweb="base-dark"]) .fii-card-text {
            color: #e0e0e0 !important;
        }
        [data-baseweb="base-dark"] ~ * .fii-card-subtext,
        [data-baseweb="base-dark"] .fii-card-subtext,
        section:has([data-baseweb="base-dark"]) .fii-card-subtext {
            color: #b0b0b0 !important;
        }
        /* Fallback para dark mode do sistema */
        @media (prefers-color-scheme: dark) {
            .fii-card-text {
                color: #e0e0e0 !important;
            }
            .fii-card-subtext {
                color: #b0b0b0 !important;
            }
        }
    </style>
    <script>
        // Função para ajustar cores baseado no tema
        function adjustColors() {
            const appContainer = document.querySelector('[data-testid="stAppViewContainer"]');
            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const isDark = appContainer && (
                appContainer.querySelector('[data-baseweb="base-dark"]') ||
                bodyBg === 'rgb(14, 17, 23)' ||
                bodyBg === 'rgb(38, 39, 48)' ||
                bodyBg.includes('rgb(14') ||
                bodyBg.includes('rgb(38') ||
                window.matchMedia('(prefers-color-scheme: dark)').matches
            );

            if (isDark):
                document.querySelectorAll('.fii-card-text').forEach(el => {
                    el.style.color = '#e0e0e0';
                });
                document.querySelectorAll('.fii-card-subtext').forEach(el => {
                    el.style.color = '#b0b0b0';
                });
            }
        }

        // Executa quando carrega e após um delay para garantir que o DOM está pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', adjustColors);
        } else {
            adjustColors();
        }

        // Executa após um pequeno delay para garantir que o Streamlit renderizou
        setTimeout(adjustColors, 200);

        // Observa mudanças no DOM
        const observer = new MutationObserver(function() {
            setTimeout(adjustColors, 50);
        });
        if (document.body) {
            observer.observe(document.body, { childList: true, subtree: true });
        }
    </script>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### 📋 {total_unread} Comunicados não lidos")

    # Cards em grid (3 colunas)
    num_cols = 3
    cols = st.columns(num_cols)

    # Função para determinar cor baseada na quantidade
    def get_color(count):
        if count == 0:
            return "#28a745"  # Verde para todos lidos
        elif count >= 8:
            return "#dc3545"  # Vermelho para muitos
        elif count >= 4:
            return "#ffc107"  # Amarelo para médio
        else:
            return "#17a2b8"  # Azul para poucos

    for idx, (ticker, count) in enumerate(unread_count.items()):
        col_idx = idx % num_cols
        color = get_color(count)

        with cols[col_idx]:
            if count == 0:
                message = "Todos comunicados lidos"
            else:
                message = f"{'comunicado' if count == 1 else 'comunicados'} não {'lido' if count == 1 else 'lidos'}"

            st.markdown(
                f"""
            <div style='padding: 15px; margin-bottom: 15px; background-color: {color}15;
                        border-left: 4px solid {color}; border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <strong class='fii-card-text' style='font-size: 18px;'>{ticker}</strong>
                    <span style='background-color: {color}; color: white; padding: 5px 12px;
                                border-radius: 20px; font-weight: bold; font-size: 16px;'>
                        {count}
                    </span>
                </div>
                <p class='fii-card-subtext' style='margin: 5px 0 0 0; font-size: 12px;'>
                    {message}
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )
