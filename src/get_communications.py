import re

import pandas as pd
from pandas.tseries.offsets import MonthEnd
from tzlocal import get_localzone

from src.constants import COMMUNICATIONS_FILE_NAME


def get_data() -> pd.DataFrame:

    df = pd.read_csv(f"downloads/{COMMUNICATIONS_FILE_NAME}.csv")

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
