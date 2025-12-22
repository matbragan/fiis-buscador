import pandas as pd
import streamlit as st

from src.constants import (
    BIG_MONEY_COLS,
    FLOAT_COLS,
    INT_COLS,
    INVESTIDOR10_BASE_URL,
    MONEY_COLS,
    PERCENT_COLS,
)
from src.get_fiis import get_data
from src.tickers import get_my_tickers, get_wanted_tickers

st.set_page_config(page_title="Buscador", layout="wide")

df = get_data()


# SIDEBAR FILTERS
atualizado = df["Data Atualização"].min().strftime("%d/%m/%Y %Hh%Mmin")
st.sidebar.text(f"Atualizado {atualizado}")


st.sidebar.header("Filtros")


tickers_list = sorted(df["Ticker"].dropna().unique())
tickers = st.sidebar.multiselect("Ticker(s)", options=tickers_list, default=None)
if tickers:
    df = df[df["Ticker"].isin(tickers)]


ordem_personalizada = ["Fundo de Tijolo", "Fundo de Papel"]
tipos_list = sorted(
    df["Tipo"].dropna().unique(),
    key=lambda x: (
        ordem_personalizada.index(x) if x in ordem_personalizada else len(ordem_personalizada)
    ),
)

tipos = st.sidebar.multiselect("Tipo(s)", options=tipos_list, default=None)
if tipos:
    df = df[df["Tipo"].isin(tipos)]


segmentos_list = sorted(df["Segmento"].dropna().unique())
segmentos = st.sidebar.multiselect("Segmento(s)", options=segmentos_list, default=None)
if segmentos:
    df = df[df["Segmento"].isin(segmentos)]


def numeric_cast(str_value):
    if str_value is None:
        return None
    str_value = str_value.replace(".", "")
    str_value = str_value.replace(",", ".")
    try:
        return float(str_value)
    except ValueError:
        return None


p_vp_min_str = st.sidebar.text_input("P/VP Mínimo")
p_vp_max_str = st.sidebar.text_input("P/VP Máximo")

p_vp_min = numeric_cast(p_vp_min_str)
p_vp_max = numeric_cast(p_vp_max_str)

if p_vp_min:
    df = df[df["P/VP"] >= p_vp_min]
if p_vp_max:
    df = df[df["P/VP"] <= p_vp_max]


dy_min_str = st.sidebar.text_input("Dividend Yield Mínimo")
dy_max_str = st.sidebar.text_input("Dividend Yield Máximo")

dy_min = numeric_cast(dy_min_str)
dy_max = numeric_cast(dy_max_str)

if dy_min:
    df = df[df["Dividend Yield"] >= dy_min]
if dy_max:
    df = df[df["Dividend Yield"] <= dy_max]


liquidez_min_str = st.sidebar.text_input("Liquidez Diária Mínima (Mil)")

liquidez_min = numeric_cast(liquidez_min_str) * 1000 if liquidez_min_str else None

if liquidez_min:
    df = df[df["Liquidez Diária"] >= liquidez_min]


st.sidebar.divider()


my_tickers = st.sidebar.toggle("Meus FIIs")
if my_tickers:
    df = df[df["Ticker"].isin(get_my_tickers())]

wanted_tickers = st.sidebar.toggle("FIIs Desejados")
if wanted_tickers:
    df = df[df["Ticker"].isin(get_wanted_tickers())]


# MAIN TABLE
st.title(f"{df.shape[0]} FIIs")

# Criar coluna com estrela para FIIs que o usuário possui
my_tickers_set = get_my_tickers()
df["⭐"] = df["Ticker"].apply(lambda x: "⭐" if x in my_tickers_set else "")

# Criar coluna Link antes de processar o dataframe
df["Link"] = df["Ticker"].apply(lambda x: f"{INVESTIDOR10_BASE_URL}{x.lower()}")

df = df.drop(columns=df.filter(regex="(approved$|rank$)").columns)
df = df.reset_index(drop=True).reset_index().rename(columns={"index": "Rank"})
df["Rank"] = df["Rank"] + 1

df = df.drop(columns=["Data Atualização"])


# Função para converter Valor Patrimonial que vem com texto (ex: "997,23 Milhões")
def convert_valor_patrimonial(value):
    """Converte Valor Patrimonial de string com texto para número"""
    if pd.isna(value) or value == "" or value == "N/A":
        return None
    if isinstance(value, (int, float)):
        return float(value)

    try:
        # Remover espaços e converter para string
        value_str = str(value).strip()

        # Verificar se contém "Bilhão" ou "Bilhões"
        if "Bilhão" in value_str or "Bilhões" in value_str:
            # Remover texto e converter formato brasileiro para número
            num_str = (
                value_str.replace("Bilhão", "").replace("Bilhões", "").replace("R$", "").strip()
            )
            num_str = num_str.replace(".", "").replace(",", ".")
            return float(num_str) * 1_000_000_000

        # Verificar se contém "Milhão" ou "Milhões"
        elif "Milhão" in value_str or "Milhões" in value_str:
            # Remover texto e converter formato brasileiro para número
            num_str = (
                value_str.replace("Milhão", "").replace("Milhões", "").replace("R$", "").strip()
            )
            num_str = num_str.replace(".", "").replace(",", ".")
            return float(num_str) * 1_000_000

        # Verificar se contém "Mil"
        elif "Mil" in value_str:
            # Remover texto e converter formato brasileiro para número
            num_str = value_str.replace("Mil", "").replace("R$", "").strip()
            num_str = num_str.replace(".", "").replace(",", ".")
            return float(num_str) * 1_000

        # Se não tem texto, tentar converter diretamente (formato brasileiro)
        else:
            num_str = str(value_str).replace("R$", "").strip()
            num_str = num_str.replace(".", "").replace(",", ".")
            return float(num_str)
    except (ValueError, AttributeError):
        return None


# Processar Valor Patrimonial antes de converter para numérico
if "Valor Patrimonial" in df.columns:
    df["Valor Patrimonial"] = df["Valor Patrimonial"].apply(convert_valor_patrimonial)

# Garantir que colunas numéricas sejam do tipo numérico (não string)
# Converter valores de string para numérico se necessário
for col in PERCENT_COLS + MONEY_COLS + BIG_MONEY_COLS + FLOAT_COLS + INT_COLS:
    if col in df.columns:
        # Para Valor Patrimonial, já foi processado acima
        if col != "Valor Patrimonial":
            df[col] = pd.to_numeric(df[col], errors="coerce")

# Configurar formatação de colunas para st.dataframe
column_config = {}

# Configurar coluna Link como link clicável com emoji
column_config["Link"] = st.column_config.LinkColumn("Link", display_text="🔗")

column_config["Rank"] = st.column_config.NumberColumn("Rank", pinned=True)

column_config["Ticker"] = st.column_config.TextColumn("Ticker", pinned=True)

column_config["⭐"] = st.column_config.TextColumn("⭐")

# Reordenar colunas para colocar estrela e Link após Ticker
cols = list(df.columns)
if "Ticker" in cols:
    ticker_idx = cols.index("Ticker")

    # Remover estrela e Link da posição atual
    if "⭐" in cols:
        cols.remove("⭐")
    if "Link" in cols:
        cols.remove("Link")

    # Inserir estrela e Link após Ticker
    insert_pos = ticker_idx + 1
    if "⭐" in df.columns:
        cols.insert(insert_pos, "⭐")
        insert_pos += 1
    if "Link" in df.columns:
        cols.insert(insert_pos, "Link")

    df = df[cols]

# Calcular altura dinamicamente baseada no número de linhas
num_rows = len(df)
calculated_height = min(num_rows * 35 + 38, 750)

df = df.style.format(
    {
        **{col: lambda x: "{:,.2f}%".format(x) for col in PERCENT_COLS},
        **{col: lambda x: "R$ {:,.2f}".format(x) for col in MONEY_COLS},
        **{col: lambda x: "R$ {:,.0f}".format(x) for col in BIG_MONEY_COLS},
        **{col: lambda x: "{:,.2f}".format(x) for col in FLOAT_COLS},
        **{col: lambda x: "{:,.0f}".format(x) for col in INT_COLS},
    },
    thousands=".",
    decimal=",",
)

st.dataframe(
    df, column_config=column_config, width="stretch", hide_index=True, height=calculated_height
)
