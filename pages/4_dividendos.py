import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import get_dividends_monthly_data, get_fiis_data
from src.utils.get_date import get_last_update_date
from src.utils.get_tickers import get_my_tickers

st.set_page_config(page_title="Dividendos Mensais", layout="wide")

st.title("Dividendos Mensais por FII")

# Sidebar - Data de atualização
atualizado = get_last_update_date()
st.sidebar.text(f"Atualizado {atualizado}")

# Verifica se há tickers cadastrados
tickers = get_my_tickers()
if not tickers:
    st.warning("⚠️ Nenhum FII cadastrado encontrado!")
    st.info(
        '💡 Acesse a página **"Meus FIIs - Quantidades"** para inserir os FIIs da sua carteira.'
    )
    st.stop()

# Carrega os dados de dividendos mensais
with st.spinner("Carregando histórico de dividendos..."):
    df_dividends_original = get_dividends_monthly_data()

if df_dividends_original.empty:
    st.warning("⚠️ Nenhum dado de dividendo encontrado!")
    st.info("💡 Os dados de dividendos são obtidos em tempo real do site Investidor10.")
    st.stop()

# Filtros
st.sidebar.header("Filtros")

# Filtro por período (range) - aplicado antes do filtro de tickers
period_options = {
    "Últimos 3 meses": 3,
    "Últimos 6 meses": 6,
    "Últimos 12 meses": 12,
    "Últimos 2 anos": 24,
    "Últimos 3 anos": 36,
    "Últimos 5 anos": 60,
    "Todos os dados": None,
}

selected_period = st.sidebar.selectbox(
    "Período",
    options=list(period_options.keys()),
    index=1,  # Default: Últimos 6 meses
)

# Calcula a data de corte baseada na seleção
df_dividends = df_dividends_original.copy()
if period_options[selected_period] is not None:
    # Obtém a data mais recente de todos os dados
    max_date_str = df_dividends_original["Ano_Mes"].max()
    max_date = pd.to_datetime(max_date_str + "-01")  # Adiciona dia 01 para criar uma data válida

    # Calcula a data de corte subtraindo os meses
    cutoff_date = max_date - pd.DateOffset(months=period_options[selected_period])
    cutoff_date_str = cutoff_date.strftime("%Y-%m")

    # Filtra os dados por período
    df_dividends = df_dividends[df_dividends["Ano_Mes"] >= cutoff_date_str]

# Carrega dados dos FIIs para obter cotações
df_fiis = get_fiis_data()

# Identifica fundos de base 10 (cotação entre R$ 8 e R$ 12)
base_10_tickers = set()
if not df_fiis.empty and "Cotação" in df_fiis.columns:
    base_10_mask = (df_fiis["Cotação"] >= 8.0) & (df_fiis["Cotação"] <= 12.0)
    base_10_tickers = set(df_fiis[base_10_mask]["Ticker"].unique())

# Filtro por Base 10 (aplicado após o filtro de período)
base_10_filter = st.sidebar.selectbox(
    "Filtro de Base",
    options=["Todos", "Fundos de Base 10", "Outros Fundos"],
    index=0,  # Default: Todos
)

if base_10_filter == "Fundos de Base 10":
    # Filtra apenas fundos de base 10
    available_tickers = set(df_dividends["Ticker"].unique())
    selected_tickers = list(available_tickers & base_10_tickers)
    if selected_tickers:
        df_dividends = df_dividends[df_dividends["Ticker"].isin(selected_tickers)]
    else:
        st.warning("⚠️ Nenhum fundo de base 10 encontrado nos dados filtrados!")
        st.stop()
elif base_10_filter == "Outros Fundos":
    # Filtra fundos que NÃO são de base 10
    available_tickers = set(df_dividends["Ticker"].unique())
    selected_tickers = list(available_tickers - base_10_tickers)
    if selected_tickers:
        df_dividends = df_dividends[df_dividends["Ticker"].isin(selected_tickers)]
    else:
        st.warning("⚠️ Nenhum outro fundo encontrado nos dados filtrados!")
        st.stop()
# Se "Todos" foi selecionado, não aplica filtro adicional

# Verifica se ainda há dados após os filtros
if df_dividends.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados!")
    st.stop()

# Gráfico de barras - Dividendos mensais por ticker
# Prepara dados para o gráfico
df_chart = df_dividends.copy()
df_chart = df_chart.sort_values(["Ano_Mes", "Ticker"])

# Cria o gráfico de barras agrupadas
fig = px.bar(
    df_chart,
    x="Mes_Ano",
    y="Valor",
    color="Ticker",
    # title="Dividendos Mensais por FII",
    labels={"Mes_Ano": "Mês/Ano", "Valor": "Valor (R$)", "Ticker": "FII"},
    barmode="group",
    hover_data={"Ano_Mes": False, "Ticker": True},
)

# Personaliza o gráfico
fig.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>"
    + "Mês: %{x}<br>"
    + "Valor: R$ %{y:,.2f}<br>"
    + "<extra></extra>",
)

fig.update_layout(
    xaxis_title="Mês/Ano",
    yaxis_title="Valor dos Dividendos (R$)",
    font=dict(size=12),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        font=dict(size=14),
    ),
    margin=dict(l=50, r=50, t=100, b=50),
    xaxis=dict(tickangle=-45),
)

st.plotly_chart(fig, use_container_width=True)
