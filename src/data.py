import re

import numpy as np
import pandas as pd
from pandas.tseries.offsets import MonthEnd
from tzlocal import get_localzone

from config.settings import (
    BIG_MONEY_COLS,
    COMMUNICATIONS_FILE,
    FLOAT_COLS,
    FUNDAMENTUS_FILE,
    INT_COLS,
    INVESTIDOR10_DIVIDENDS_FILE,
    INVESTIDOR10_FILE,
    MONEY_COLS,
    PERCENT_COLS,
    WARD_FILE,
)


def join_scrapes() -> pd.DataFrame:
    """
    Junta os dados obtidos dos scrapes dos sites Investidor10 e Fundamentus.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs.
    """
    investidor10_df = pd.read_csv(INVESTIDOR10_FILE)
    fundamentus_df = pd.read_csv(FUNDAMENTUS_FILE)

    fundamentus_df = fundamentus_df.rename(columns={"Papel": "Ticker"})
    fundamentus_df = fundamentus_df[["Ticker", "Qtd de imóveis", "Valor de Mercado"]]

    df = investidor10_df.merge(fundamentus_df, how="left", on="Ticker")

    return df


def get_fiis_data() -> pd.DataFrame:
    """
    Obtem os dados de FIIs do site Investidor10 - obtidos através do scrape -
    e adiciona com alguns dados do Fundamentus.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs.
    """
    df = join_scrapes()

    cols_to_fill = df.columns.difference(
        PERCENT_COLS + MONEY_COLS + BIG_MONEY_COLS + FLOAT_COLS + INT_COLS
    )
    df[cols_to_fill] = df[cols_to_fill].fillna("")

    df["Último Yield"] = (df["Último Rendimento"] / df["Cotação"] * 100).where(
        df["Cotação"] != 0, 0
    )

    df["Cálculo Valor de Mercado"] = df["Cotação"] * df["Cotas Emitidas"]
    df["Valor de Mercado"] = df["Cálculo Valor de Mercado"].where(
        df["Cálculo Valor de Mercado"] != 0, df["Valor de Mercado"]
    )
    df["Valor de Mercado"] = df["Valor de Mercado"].astype(float)

    df["Qtd de imóveis"] = df["Qtd de imóveis"].fillna(0).astype(int)

    df = df[df["Dados Obtidos"]]
    df = df[
        [
            "Ticker",
            "Tipo",
            "Segmento",
            "Cotação",
            "P/VP",
            "Dividend Yield",
            "Último Rendimento",
            "Último Yield",
            "Liquidez Diária",
            "Qtd de imóveis",
            "Vacância",
            "Variação 12M",
            "Tipo de Gestão",
            "Valor de Mercado",
            "Valor Patrimonial",
            "Número de Cotistas",
            "Público Alvo",
            "Taxa de Administração",
            "Data Atualização",
        ]
    ]

    try:
        ward_fiis = pd.read_csv(WARD_FILE)
        ward_fiis = ward_fiis.rename(columns={"Segmento": "Segmento2"})
        df = df.merge(ward_fiis, how="left", on="Ticker")
        condition = df["Segmento2"].isnull()
        df["Segmento2"] = np.where(condition, df["Segmento"], df["Segmento2"])
        condition = df["Segmento"].isin(["Outros", "Híbrido"])
        df["Segmento"] = np.where(condition, df["Segmento2"], df["Segmento"])
        replacements = {
            "Logístico / Indústria / Galpões": "Logística",
            "Industrial": "Logística",
            "Shoppings / Varejo": "Shoppings",
            "Varejo": "Renda Urbana",
            "Títulos e Valores Mobiliários": "Títulos e Val. Mob.",
            "Papel CRI": "Títulos e Val. Mob.",
            "Fundo de Infraestrutura (FI-Infra)": "FI-Infra",
            "Fundo de Investimentos em Participações (FIP)": "FIP",
            "Outro": "Outros",
            "Híbrido": "Outros",
        }
        df["Segmento"] = df["Segmento"].replace(replacements)
        df = df.drop(columns=["Segmento2"])

        type_segment_dict = {
            "Agrícola": "Fundo de Tijolo",
            "Agências bancárias": "Fundo de Tijolo",
            "Cemitério": "Fundo de Tijolo",
            "Desenvolvimento": "Fundo de Desenvolvimento",
            "Educacional": "Fundo de Tijolo",
            "FI-Infra": "Outro",
            "FIP": "Outro",
            "Fiagros": "Outro",
            "Fundo de Fundos": "Fundo de Fundos",
            "Hospitalar": "Fundo de Tijolo",
            "Hotéis": "Fundo de Tijolo",
            "Lajes Corporativas": "Fundo de Tijolo",
            "Logística": "Fundo de Tijolo",
            "Renda Urbana": "Fundo de Tijolo",
            "Residencial": "Fundo de Tijolo",
            "Shoppings": "Fundo de Tijolo",
        }

        # Substituir Tipo baseado no Segmento usando o dicionário
        df["Tipo"] = df.apply(
            lambda row: type_segment_dict.get(row["Segmento"], row["Tipo"]), axis=1
        )

    except Exception:
        pass

    df["dy_rank"] = df["Dividend Yield"].rank(ascending=False) * 2
    df["p_vp_rank"] = df["P/VP"].rank()
    df["rank"] = df["dy_rank"] + df["p_vp_rank"]
    df = df.sort_values(by="rank")

    local_tz = get_localzone()
    df["Data Atualização"] = (
        pd.to_datetime(df["Data Atualização"])
        .dt.tz_localize(local_tz)
        .dt.tz_convert("America/Sao_Paulo")
    )

    return df


def get_communications_data() -> pd.DataFrame:
    """
    Obtém os dados de comunicações dos FIIs.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados de comunicações.
    """
    df = pd.read_csv(COMMUNICATIONS_FILE)

    df.fillna("-", inplace=True)

    local_tz = get_localzone()
    df["Data Atualização"] = (
        pd.to_datetime(df["Data Atualização"])
        .dt.tz_localize(local_tz)
        .dt.tz_convert("America/Sao_Paulo")
    )

    def parse_data_referencia(value):
        value = str(value).strip()
        # Se for do tipo "mm/yyyy", aplica tratamento especial
        if re.fullmatch(r"\d{2}/\d{4}", value):
            return pd.to_datetime(value, format="%m/%Y") + MonthEnd(1)
        else:
            return pd.to_datetime(value, dayfirst=True)

    df["Data de Referência"] = df["Data de Referência"].apply(parse_data_referencia)

    df["Data de Entrega"] = pd.to_datetime(df["Data de Entrega"], dayfirst=True)

    df = df.sort_values(by=["Ticker", "Data de Entrega", "Versão"], ascending=[True, False, False])

    df["Mês de Referência"] = df["Data de Referência"].dt.strftime("%B").str.capitalize()
    df["Data de Referência"] = df["Data de Referência"].dt.strftime("%Y/%m/%d")
    df["Data de Entrega"] = df["Data de Entrega"].dt.strftime("%Y/%m/%d %Hh%Mmin")

    return df


def get_dividends_monthly_data() -> pd.DataFrame:
    """
    Obtém o histórico de dividendos mensais de todos os FIIs do usuário.
    Lê os dados do arquivo CSV gerado pelo scrape e agrega os dividendos por ticker e mês.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dividendos mensais agregados com as colunas:
            - Ticker: Ticker do FII
            - Ano_Mes: Ano e mês no formato YYYY-MM
            - Mes_Ano: Mês e ano no formato MM/YYYY para exibição
            - Valor: Soma dos dividendos do mês
    """
    try:
        df_dividends = pd.read_csv(INVESTIDOR10_DIVIDENDS_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Ticker", "Ano_Mes", "Mes_Ano", "Valor"])

    if df_dividends.empty:
        return pd.DataFrame(columns=["Ticker", "Ano_Mes", "Mes_Ano", "Valor"])

    # Converte data_com para datetime se ainda não for
    if df_dividends["data_com"].dtype == "object":
        df_dividends["data_com"] = pd.to_datetime(df_dividends["data_com"])

    # Remove linhas onde data_com é None
    df_dividends = df_dividends[df_dividends["data_com"].notna()].copy()

    if df_dividends.empty:
        return pd.DataFrame(columns=["Ticker", "Ano_Mes", "Mes_Ano", "Valor"])

    # Extrai ano e mês da coluna data_com
    df_dividends["Ano_Mes"] = df_dividends["data_com"].dt.to_period("M")
    df_dividends["Ano_Mes"] = df_dividends["Ano_Mes"].astype(str)

    # Cria coluna para exibição no formato MM/YYYY
    df_dividends["Mes_Ano"] = df_dividends["data_com"].dt.strftime("%m/%Y")

    # Agrega por Ticker e Ano_Mes, somando os valores
    df_aggregated = (
        df_dividends.groupby(["Ticker", "Ano_Mes", "Mes_Ano"])["valor"]
        .sum()
        .reset_index()
        .rename(columns={"valor": "Valor"})
    )

    # Ordena por Ticker e Ano_Mes
    df_aggregated = df_aggregated.sort_values(["Ticker", "Ano_Mes"])

    return df_aggregated
