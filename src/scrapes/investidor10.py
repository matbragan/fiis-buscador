"""
Scraper para obter dados dos FIIs do site Investidor10.
"""

import logging
import re
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config.settings import HEADERS, INVESTIDOR10_BASE_URL, INVESTIDOR10_FILE
from src.utils.write_files import write_csv_file

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


class Investidor10Scraper:
    """Classe para obter dados dos FIIs do site Investidor10."""

    def __init__(self):
        self.base_url = INVESTIDOR10_BASE_URL
        self.headers = HEADERS

    def get_soup_request(self, route: str) -> BeautifulSoup:
        """
        Cria um BeautifulSoup de acordo com a rota passada na url base.
        """
        url = self.base_url + route
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return BeautifulSoup(response.text, "html.parser")
        else:
            logging.error(f"Erro na requisição: {response.status_code} - rota: {route}")
            return None

    def find_metric_by_string(self, string: str, soup: BeautifulSoup) -> str:
        """
        Encontra uma métrica em um BeautifulSoup baseado em uma string.
        """
        metric = soup.find("span", string=string)
        metric = metric.find_next("span").text.strip() if metric else "N/A"
        return metric

    def find_metric_by_re(self, re_string: str, soup: BeautifulSoup) -> str:
        """
        Encontra uma métrica em um BeautifulSoup baseado em uma string de regex.
        """
        metric = soup.find("span", string=re.compile(re_string, re.IGNORECASE))
        metric = (
            metric.find_parent("div", class_="desc")
            .find("div", class_="value")
            .find("span")
            .get_text(strip=True)
            if metric
            else "N/A"
        )
        return metric

    def convert_metric_to_float(self, metric: str, multiplier: int = 1) -> float:
        """
        Converte uma métrica de string para float, removendo caracteres não numéricos e substituindo vírgulas por pontos.
        """
        if metric not in ["-", "N/A", "", "R$ -"]:
            metric = metric.replace("R$", "").replace("%", "").replace(" ", "")
            metric = metric.replace(".", "").replace(",", ".")
            return float(metric) * multiplier
        else:
            return 0

    def find_cell_by_data_name(self, cells: list, data_name: str) -> BeautifulSoup:
        """
        Encontra uma célula em uma lista de BeautifulSoup baseado em um data-name.
        """
        for cell in cells:
            if cell.get("data-name") == data_name:
                return cell
        return None

    def get_unique_fii_data(self, ticker: str) -> list:
        """
        Obtém os dados de um único FII, baseado em seu ticker e fazendo a requisição no Investidor10.
        Transforma valores que representam dados numéricos em float e com pontos e virgulas no estilo EUA.

        Args:
            ticker (str): Ticker do FII que se deseja obter os dados.

        Returns:
            list: Uma lista com os dados do FII.
        """
        route = ticker.lower()
        soup = self.get_soup_request(route=route)

        if not soup:
            logging.error(f"Erro ao obter dados do FII {ticker}")
            return []

        # Cotação
        cotacao = self.find_metric_by_string(string=f"{ticker.upper()} Cotação", soup=soup)
        cotacao = self.convert_metric_to_float(metric=cotacao)

        # Liquidez Diária
        liquidez = self.find_metric_by_string(string="Liquidez Diária", soup=soup)
        if liquidez.endswith("M"):
            multiplier = 1_000_000
            liquidez = liquidez.replace("M", "")
        elif liquidez.endswith("K"):
            multiplier = 1_000
            liquidez = liquidez.replace("K", "")
        liquidez = self.convert_metric_to_float(metric=liquidez, multiplier=multiplier)

        # Variação 12M
        variacao12m = self.find_metric_by_string(string="VARIAÇÃO (12M)", soup=soup)
        variacao12m = self.convert_metric_to_float(metric=variacao12m)

        # CNPJ
        cnpj = self.find_metric_by_re(re_string=r"CNPJ", soup=soup)
        cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "")

        # Público Alvo
        publico_alvo = self.find_metric_by_re(re_string=r"PÚBLICO-ALVO", soup=soup)
        match publico_alvo:
            case "fii.QUALIFIED_INVESTOR":
                publico_alvo = "Investidor Qualificado"
            case "fii.GENERAL":
                publico_alvo = "Geral"
            case _:
                pass

        # Segmento
        segmento = self.find_metric_by_re(re_string=r"SEGMENTO", soup=soup)

        # Tipo de Gestão
        tipo_gestao = self.find_metric_by_re(re_string=r"TIPO DE GESTÃO", soup=soup)
        match tipo_gestao:
            case "Passive":
                tipo_gestao = "Passiva"
            case "fii.PASSIVE":
                tipo_gestao = "Passiva"
            case "Active":
                tipo_gestao = "Ativa"
            case "fii.ACTIVE":
                tipo_gestao = "Ativa"
            case _:
                pass

        # Taxa de Administração
        taxa_adm = self.find_metric_by_re(re_string=r"TAXA DE ADMINISTRAÇÃO", soup=soup)

        # Vacância
        vacancia = self.find_metric_by_re(re_string=r"VACÂNCIA", soup=soup)
        vacancia = self.convert_metric_to_float(metric=vacancia)

        # Número de Cotistas
        nro_cotistas = self.find_metric_by_re(re_string=r"NUMERO DE COTISTAS", soup=soup)
        nro_cotistas = self.convert_metric_to_float(metric=nro_cotistas)

        # Cotas Emitidas
        cotas_emitidas = self.find_metric_by_re(re_string=r"COTAS EMITIDAS", soup=soup)
        cotas_emitidas = self.convert_metric_to_float(metric=cotas_emitidas)

        # Valor Patrimonial
        vl_patrimonial = self.find_metric_by_re(re_string=r"VALOR PATRIMONIAL", soup=soup)
        if "Bilhão" in vl_patrimonial or "Bilhões" in vl_patrimonial:
            multiplier = 1_000_000_000
            vl_patrimonial = vl_patrimonial.replace("Bilhão", "").replace("Bilhões", "")
        elif "Milhão" in vl_patrimonial or "Milhões" in vl_patrimonial:
            multiplier = 1_000_000
            vl_patrimonial = vl_patrimonial.replace("Milhão", "").replace("Milhões", "")
        elif "Mil" in vl_patrimonial or "Mils" in vl_patrimonial:
            multiplier = 1_000
            vl_patrimonial = vl_patrimonial.replace("Mil", "").replace("Mils", "")
        vl_patrimonial = self.convert_metric_to_float(metric=vl_patrimonial, multiplier=multiplier)

        # Último Rendimento
        ult_rendimento = self.find_metric_by_re(re_string=r"ÚLTIMO RENDIMENTO", soup=soup)
        ult_rendimento = self.convert_metric_to_float(metric=ult_rendimento)

        return [
            cotacao,
            liquidez,
            variacao12m,
            cnpj,
            publico_alvo,
            segmento,
            tipo_gestao,
            taxa_adm,
            vacancia,
            nro_cotistas,
            cotas_emitidas,
            vl_patrimonial,
            ult_rendimento,
        ]

    def _parse_date_string(self, date_str: str, ticker: str, field_name: str) -> datetime | None:
        """
        Converte uma string de data no formato DD/MM/YYYY para datetime.

        Args:
            date_str: String da data no formato DD/MM/YYYY
            ticker: Ticker do FII para logging
            field_name: Nome do campo para logging

        Returns:
            datetime ou None se a conversão falhar
        """
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            logging.warning(f"Erro ao converter {field_name} '{date_str}' para o FII {ticker}")
            return None

    def _parse_dividend_row(self, row, ticker: str) -> dict | None:
        """
        Extrai dados de uma linha da tabela de dividendos.

        Args:
            row: Elemento BeautifulSoup representando uma linha da tabela
            ticker: Ticker do FII para logging

        Returns:
            Dicionário com os dados do dividendo ou None se a linha for inválida
        """
        cells = row.find_all("td")
        if len(cells) < 4:
            return None

        # Extrai os dados de cada célula
        tipo = cells[0].get_text(strip=True)
        data_com_str = cells[1].get_text(strip=True)
        pagamento_str = cells[2].get_text(strip=True)
        valor_str = cells[3].get_text(strip=True)

        # Converte datas
        data_com = self._parse_date_string(data_com_str, ticker, "data_com")
        pagamento = self._parse_date_string(pagamento_str, ticker, "pagamento")

        # Converte valor de formato brasileiro (0,11000000) para float
        valor = self.convert_metric_to_float(metric=valor_str)

        return {
            "tipo": tipo,
            "data_com": data_com,
            "pagamento": pagamento,
            "valor": valor,
        }

    def get_dividend_history(self, ticker: str) -> pd.DataFrame:
        """
        Obtém o histórico de dividendos de um FII específico.

        Args:
            ticker (str): Ticker do FII que se deseja obter o histórico de dividendos.

        Returns:
            pd.DataFrame: Um DataFrame contendo o histórico de dividendos com as colunas:
                - tipo: Tipo de distribuição (ex: Dividendos)
                - data_com: Data com (ex-date)
                - pagamento: Data de pagamento
                - valor: Valor do dividendo
        """
        route = ticker.lower()
        soup = self.get_soup_request(route=route)

        if not soup:
            logging.error(f"Erro ao obter dados do FII {ticker}")
            return pd.DataFrame()

        # Encontra a tabela de histórico de dividendos
        table = soup.find("table", id="table-dividends-history")
        if not table:
            logging.warning(f"Tabela de dividendos não encontrada para o FII {ticker}")
            return pd.DataFrame()

        # Encontra todas as linhas do tbody
        tbody = table.find("tbody")
        if not tbody:
            logging.warning(f"Tbody não encontrado na tabela de dividendos do FII {ticker}")
            return pd.DataFrame()

        rows = tbody.find_all("tr")
        data = []

        for row in rows:
            dividend_data = self._parse_dividend_row(row, ticker)
            if dividend_data:
                data.append(dividend_data)

        df = pd.DataFrame(data)

        if not df.empty:
            logging.info(
                f"Histórico de dividendos do FII {ticker} obtido com sucesso! ({len(df)} registros)"
            )
        else:
            logging.warning(f"Nenhum registro de dividendo encontrado para o FII {ticker}")

        return df

    def get_all_dividends(self, tickers: list) -> pd.DataFrame:
        """
        Obtém o histórico de dividendos de uma lista de FIIs.

        Args:
            tickers (list): Lista de tickers dos FIIs que se deseja obter o histórico de dividendos.

        Returns:
            pd.DataFrame: Um DataFrame contendo o histórico de dividendos de todos os FIIs com as colunas:
                - Ticker: Ticker do FII
                - tipo: Tipo de distribuição (ex: Dividendos)
                - data_com: Data com (ex-date)
                - pagamento: Data de pagamento
                - valor: Valor do dividendo
                - Data Atualização: Data da atualização dos dados
        """
        all_dividends = []

        logging.info(f"Iniciando coleta de dividendos para {len(tickers)} FIIs...")

        for ticker in tickers:
            try:
                df_dividends = self.get_dividend_history(ticker=ticker)

                if not df_dividends.empty:
                    df_dividends["Ticker"] = ticker
                    all_dividends.append(df_dividends)

            except Exception as e:
                logging.error(f"Erro ao obter dividendos do FII {ticker}: {str(e)}")
                continue

        if not all_dividends:
            logging.warning("Nenhum dado de dividendo foi obtido")
            return pd.DataFrame(
                columns=["Ticker", "tipo", "data_com", "pagamento", "valor", "Data Atualização"]
            )

        # Concatena todos os DataFrames
        df_all = pd.concat(all_dividends, ignore_index=True)
        df_all["Data Atualização"] = datetime.now()

        logging.info(
            f"✓ Coleta de dividendos concluída! ({len(df_all)} registros de {len(tickers)} FIIs)"
        )

        return df_all

    def get_fiis_from_page(self, page: int) -> pd.DataFrame:
        """
        Obtém os dados dos FIIs de uma determinada página no site Investidor10.
        Obtém tantos os dados vindos na página quanto os dados adicionais do FII, baseado em seu ticker.

        Args:
            page (int): A página para se obter os FIIs.

        Returns:
            pd.DataFrame: Um DataFrame contendo os FIIs.
        """
        route = f"?page={page}"
        soup = self.get_soup_request(route=route)

        if not soup:
            logging.error(f"Erro ao obter dados da página {page}")
            return pd.DataFrame()

        table = soup.find("table", id="rankigns")
        if not table:
            logging.error(f"Tabela não encontrada na página {page}")
            return pd.DataFrame()

        rows = table.find("tbody").find_all("tr") if table.find("tbody") else []
        data = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 6:
                continue

            # Ticker e Nome
            ativos_cell = cells[0]

            # Ticker
            ticker_span = ativos_cell.find("span", class_="font-semibold")
            if not ticker_span:
                continue
            ticker = ticker_span.text.strip()

            # Nome
            nome_spans = ativos_cell.find_all("span")
            nome = "N/A"
            for span in nome_spans:
                if span.text.strip() != ticker and "truncate" in span.get("class", []):
                    nome = span.text.strip()
                    break

            # P/VP
            p_vp_cell = self.find_cell_by_data_name(cells=cells, data_name="p_vp")
            p_vp_div = p_vp_cell.find("div", class_="decimal")
            p_vp_text = p_vp_div.text.strip() if p_vp_div else "N/A"
            p_vp = self.convert_metric_to_float(metric=p_vp_text)

            # Dividend Yield
            dy_cell = self.find_cell_by_data_name(
                cells=cells, data_name="dividend_yield_last_12_months"
            )
            dy_div = dy_cell.find("div", class_="percent")
            dy_text = dy_div.text.strip() if dy_div else "N/A"
            dy = self.convert_metric_to_float(metric=dy_text)

            # Tipo
            tipo_cell = self.find_cell_by_data_name(cells=cells, data_name="fii_type")
            tipo_div = tipo_cell.find("div", class_="text")
            tipo_text = tipo_div.text.strip() if tipo_div else "N/A"
            match tipo_text:
                case "Fundo de tijolo":
                    tipo = "Fundo de Tijolo"
                case "Fundo de papel":
                    tipo = "Fundo de Papel"
                case "Fundo de desenvolvimento":
                    tipo = "Fundo de Desenvolvimento"
                case "Fundo de fundos":
                    tipo = "Fundo de Fundos"
                case "Fundo misto":
                    tipo = "Fundo Misto"
                case "-":
                    tipo = "Outro"
                case _:
                    tipo = tipo_text

            # Juntando dados básicos e dados adicionais
            basic_data = [ticker, nome, p_vp, dy, tipo]
            plus_data = self.get_unique_fii_data(ticker=ticker)
            get_plus_data = True if len(plus_data) != 0 else False
            data.append(basic_data + [get_plus_data] + plus_data)

        columns = [
            "Ticker",
            "Nome",
            "P/VP",
            "Dividend Yield",
            "Tipo",
            "Dados Obtidos",
            "Cotação",
            "Liquidez Diária",
            "Variação 12M",
            "CNPJ",
            "Público Alvo",
            "Segmento",
            "Tipo de Gestão",
            "Taxa de Administração",
            "Vacância",
            "Número de Cotistas",
            "Cotas Emitidas",
            "Valor Patrimonial",
            "Último Rendimento",
        ]

        # Preenchendo colunas vazias
        for i in range(len(data)):
            if len(data[i]) < len(columns):
                data[i] += [None] * (len(columns) - len(data[i]))

        df = pd.DataFrame(data, columns=columns)

        logging.info(
            f"Leitura de FIIs da página {page} feita com sucesso! ({len(df)} FIIs obtidos)"
        )
        return df

    def main(self) -> pd.DataFrame:
        """
        Obtém os dados de todos os FIIs do site Investidor10.

        Returns:
            pd.DataFrame: Um DataFrame contendo todos os FIIs do site.
        """
        all_fiis = pd.DataFrame()

        logging.info("Leitura de FIIs do site Investidor10 iniciando...")
        for page in range(1, 16):
            fiis = self.get_fiis_from_page(page=page)
            if fiis.empty:
                break
            all_fiis = pd.concat([all_fiis, fiis], ignore_index=True)

        all_fiis["Data Atualização"] = datetime.now()

        logging.info("✓ Leitura de FIIs do site Investidor10 concluída!")
        return all_fiis


if __name__ == "__main__":
    FIIsScraper = Investidor10Scraper()
    fiis = FIIsScraper.main()

    write_csv_file(data=fiis, file_path=INVESTIDOR10_FILE)
