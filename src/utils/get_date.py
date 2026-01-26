import pandas as pd
import streamlit as st

from src.data import get_communications_data, get_fiis_data


@st.cache_data(ttl=0)  # Cache com TTL 0 para permitir invalidação manual
def _get_fiis_data_cached():
    """Wrapper cached para get_fiis_data"""
    return get_fiis_data()


@st.cache_data(ttl=0)  # Cache com TTL 0 para permitir invalidação manual
def _get_communications_data_cached():
    """Wrapper cached para get_communications_data"""
    return get_communications_data()


def get_last_update_date(
    fiis_data: pd.DataFrame | None = None,
    communications_data: pd.DataFrame | None = None,
    use_cache: bool = True,
) -> str:
    """
    Obtém a data da última atualização dos dados dos FIIs e comunicados.

    Args:
        fiis_data: DataFrame opcional com dados dos FIIs. Se None, carrega os dados.
        communications_data: DataFrame opcional com dados de comunicados. Se None, carrega os dados.
        use_cache: Se True, usa cache do Streamlit. Se False, força recarregamento dos dados.
    """
    # Se não foram fornecidos, carrega os dados
    if fiis_data is None:
        if use_cache:
            fiis_data = _get_fiis_data_cached()
        else:
            fiis_data = get_fiis_data()
    if communications_data is None:
        if use_cache:
            communications_data = _get_communications_data_cached()
        else:
            communications_data = get_communications_data()

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
