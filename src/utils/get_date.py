import pandas as pd

from src.data import get_communications_data, get_fiis_data


def get_last_update_date(
    fiis_data: pd.DataFrame = get_fiis_data(),
    communications_data: pd.DataFrame = get_communications_data(),
) -> str:
    """
    Obtém a data da última atualização dos dados dos FIIs e comunicados.
    """
    fiis_date = (
        fiis_data["Data Atualização"].min().strftime("%d/%m/%Y %Hh%Mmin")
        if not fiis_data.empty
        else "-"
    )
    communications_date = (
        communications_data["Data Atualização"].min().strftime("%d/%m/%Y %Hh%Mmin")
        if not communications_data.empty
        else "-"
    )
    return min(fiis_date, communications_date)
