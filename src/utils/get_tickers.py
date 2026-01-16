import json
import os

import pandas as pd

from config.settings import INVESTIDOR10_FILE, MY_FIIS_FILE, WANTED_FIIS_FILE


def get_my_tickers():
    """Retorna um set com os tickers dos FIIs que o usuário possui (carregados do arquivo JSON)"""
    file_path = MY_FIIS_FILE
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            quantities = json.load(f)
            return set(quantities.keys())
    return set()


def get_wanted_tickers():
    """Retorna um set com os tickers dos FIIs desejados (carregados do arquivo JSON)"""
    file_path = WANTED_FIIS_FILE
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            wanted_fiis = json.load(f)
            return set(wanted_fiis.keys())
    return set()


def get_tickers_with_cnpj():
    """Retorna um dicionário com ticker: CNPJ para todos os FIIs cadastrados (meus + desejados)"""
    tickers_dict = {}

    # Busca CNPJs do arquivo CSV do investidor10
    # Tenta diferentes caminhos possíveis
    possible_paths = [
        INVESTIDOR10_FILE,
        os.path.join(os.path.dirname(os.path.dirname(__file__)), INVESTIDOR10_FILE),
        os.path.join(os.getcwd(), INVESTIDOR10_FILE),
    ]

    investidor10_file = None
    for path in possible_paths:
        if os.path.exists(path):
            investidor10_file = path
            break

    if investidor10_file:
        try:
            df = pd.read_csv(investidor10_file)
            if "CNPJ" in df.columns and "Ticker" in df.columns:
                # Converte CNPJ para string para evitar problemas com tipos numéricos
                df["CNPJ"] = df["CNPJ"].astype(str)
                cnpj_map = dict(zip(df["Ticker"], df["CNPJ"]))

                # Adiciona FIIs que o usuário possui
                my_tickers = get_my_tickers()
                for ticker in my_tickers:
                    cnpj = cnpj_map.get(ticker, "")
                    # Garante que CNPJ seja string
                    tickers_dict[ticker] = str(cnpj) if pd.notna(cnpj) and cnpj != "nan" else ""

                # Adiciona FIIs desejados
                wanted_tickers = get_wanted_tickers()
                for ticker in wanted_tickers:
                    if ticker not in tickers_dict:
                        cnpj = cnpj_map.get(ticker, "")
                        # Garante que CNPJ seja string
                        tickers_dict[ticker] = str(cnpj) if pd.notna(cnpj) and cnpj != "nan" else ""
        except Exception:
            pass

    return tickers_dict
