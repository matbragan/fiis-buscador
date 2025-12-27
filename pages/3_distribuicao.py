import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import MY_FIIS_FILE
from src.get_fiis import get_data
from src.tickers import get_my_tickers

st.set_page_config(page_title="Distribuição", layout="wide")

# Carrega os dados dos FIIs
df = get_data()
df = df[df["Ticker"].isin(get_my_tickers())].sort_values("Ticker")


# CARREGAMENTO DAS QUANTIDADES


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


# Carrega as quantidades
quantities = load_quantities()

# VERIFICAÇÃO DE DADOS

if not quantities or all(qty == 0 for qty in quantities.values()):
    st.warning("⚠️ Nenhuma quantidade de FII foi encontrada!")
    st.info(
        '💡 Acesse a página **"Meus FIIs - Quantidades"** para inserir as quantidades dos seus FIIs.'
    )
    st.stop()

# Filtra apenas FIIs com quantidade > 0
active_fiis = {ticker: qty for ticker, qty in quantities.items() if qty > 0}

if not active_fiis:
    st.warning("⚠️ Nenhum FII com quantidade maior que zero encontrado!")
    st.info(
        '💡 Acesse a página **"Meus FIIs - Quantidades"** para inserir as quantidades dos seus FIIs.'
    )
    st.stop()

# RESUMO GERAL

col1, col2, col3, col4, col5 = st.columns(5)

# Calcula métricas gerais
total_investido = sum(
    qty * df[df["Ticker"] == ticker].iloc[0]["Cotação"]
    for ticker, qty in active_fiis.items()
    if not df[df["Ticker"] == ticker].empty
)

total_cotas = sum(active_fiis.values())
total_fiis = len(active_fiis)

# Calcula DY médio ponderado
dy_ponderado = 0
ultimo_yield_ponderado = 0
for ticker, qty in active_fiis.items():
    fii_data = df[df["Ticker"] == ticker]
    if not fii_data.empty:
        valor_fii = qty * fii_data.iloc[0]["Cotação"]
        peso = valor_fii / total_investido
        dy_fii = fii_data.iloc[0]["Dividend Yield"]
        ultimo_yield_fii = fii_data.iloc[0]["Último Yield"]
        dy_ponderado += peso * dy_fii
        ultimo_yield_ponderado += peso * ultimo_yield_fii

with col1:
    st.metric(
        "💰 Total Investido",
        f"R$ {total_investido:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", "."),
    )
with col2:
    st.metric(
        "📈 Total de Cotas",
        f"{total_cotas:,}".replace(",", "TEMP").replace(".", ",").replace("TEMP", "."),
    )
with col3:
    st.metric("🏢 FIIs na Carteira", f"{total_fiis}")
with col4:
    st.metric("🪃 DY Médio Ponderado", f"{dy_ponderado:.2f}%".replace(".", ","))
with col5:
    st.metric("📊 Último Yield Ponderado", f"{ultimo_yield_ponderado:.2f}%".replace(".", ","))

# GRÁFICO DE DISTRIBUIÇÃO POR SEGMENTO

# Calcula o valor por segmento
segmento_data = {}
for ticker, qty in active_fiis.items():
    fii_data = df[df["Ticker"] == ticker]
    if not fii_data.empty:
        segmento = fii_data.iloc[0]["Segmento"]
        cotacao = fii_data.iloc[0]["Cotação"]
        valor_total = qty * cotacao

        if segmento in segmento_data:
            segmento_data[segmento] += valor_total
        else:
            segmento_data[segmento] = valor_total

if segmento_data:
    # Cria DataFrame para o gráfico
    df_segmento = pd.DataFrame(list(segmento_data.items()), columns=["Segmento", "Valor Total"])
    df_segmento = df_segmento.sort_values("Valor Total", ascending=False)

    # Calcula percentuais
    df_segmento["Percentual"] = (
        df_segmento["Valor Total"] / df_segmento["Valor Total"].sum() * 100
    ).round(2)

    # Define paleta de cores consistente
    cores_paleta = px.colors.qualitative.Set3

    # Cria mapeamento de cores para segmentos
    segmentos_unicos = df_segmento["Segmento"].unique()
    color_map = {
        segmento: cores_paleta[i % len(cores_paleta)] for i, segmento in enumerate(segmentos_unicos)
    }

    # Cria o gráfico de pizza
    fig_pizza = px.pie(
        df_segmento,
        values="Valor Total",
        names="Segmento",
        title="Distribuição do Patrimônio por Segmento",
        color="Segmento",
        color_discrete_map=color_map,
    )

    # Personaliza o gráfico
    fig_pizza.update_traces(
        textposition="outside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>"
        + "Valor: R$ %{value:,.2f}<br>"
        + "Percentual: %{percent}<br>"
        + "<extra></extra>",
    )

    fig_pizza.update_layout(
        font=dict(size=14),
        showlegend=True,
        legend=dict(
            orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.01, font=dict(size=16)
        ),
        margin=dict(l=50, r=50, t=50, b=50),
    )

    st.plotly_chart(fig_pizza, width="stretch")

# GRÁFICO DE BARRAS POR FII

# Prepara dados para gráfico de barras
fiis_data = []
for ticker, qty in active_fiis.items():
    fii_data = df[df["Ticker"] == ticker]
    if not fii_data.empty:
        fii_row = fii_data.iloc[0]
        valor_total = qty * fii_row["Cotação"]
        percentual = (
            valor_total / total_investido
        ) * 100  # Usa o mesmo total_investido que funciona

        fiis_data.append(
            {
                "Ticker": ticker,
                "Segmento": fii_row["Segmento"],
                "Valor Total": valor_total,
                "Percentual": percentual,
                "Quantidade": qty,
                "Cotação": fii_row["Cotação"],
                "DY": fii_row["Dividend Yield"],
            }
        )

df_fiis = pd.DataFrame(fiis_data)
df_fiis = df_fiis.sort_values("Valor Total", ascending=False)  # Ordena do maior para o menor

# Adiciona coluna de texto para as barras diretamente no DataFrame
df_fiis["Percentual_Texto"] = df_fiis["Percentual"].apply(lambda x: f"{x:.1f}%")

# Cria o gráfico com dados adicionais para o tooltip
fig_barras = px.bar(
    df_fiis,
    x="Valor Total",
    y="Ticker",
    color="Segmento",
    title="Valor Investido por FII",
    color_discrete_map=color_map,  # Usa o mesmo mapeamento de cores
    orientation="h",
    text="Percentual_Texto",  # Usa diretamente a coluna do DataFrame
    hover_data={"Quantidade": True, "DY": ":.2f", "Cotação": ":.2f", "Segmento": True},
)

# Atualiza o tooltip personalizado e posição do texto
fig_barras.update_traces(
    hovertemplate="<b>%{y}</b><br>"
    + "Valor Total: R$ %{x:,.2f}<br>"
    + "Quantidade: %{customdata[0]} cotas<br>",
    textposition="inside",
)

fig_barras.update_layout(
    xaxis_title="Valor Investido (R$)",
    yaxis_title="",
    font=dict(size=12),
    yaxis={"categoryorder": "total ascending"},  # Ordena do maior valor para o menor
)

st.plotly_chart(fig_barras, width="stretch")

# INFORMAÇÕES ADICIONAIS

atualizado = df["Data Atualização"].min().strftime("%d/%m/%Y %Hh%Mmin")
st.sidebar.text(f"Atualizado {atualizado}")
