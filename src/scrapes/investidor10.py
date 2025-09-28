import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import re
import logging
from datetime import datetime

import requests
import pandas as pd
from bs4 import BeautifulSoup

from src.constants import INVESTIDOR10_BASE_URL, HEADERS, INVESTIDOR10_FILE_NAME
from src.utils import write_csv_file


log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


class Investidor10Scraper:
    ''' Classe para obter dados dos FIIs do site Investidor10. '''
    def __init__(self):
        self.base_url = INVESTIDOR10_BASE_URL
        self.headers = HEADERS

    
    def get_soup_request(self, route: str) -> BeautifulSoup:
        '''
        Cria um BeautifulSoup de acordo com a rota ou filtro passado na requisição.

        Args:
            route (str): Rota ou filtro para fazer a requisição na url base

        Returns:
            BeautifulSoup: Objeto BeautifulSoup
        '''
        url = self.base_url + route
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
        else:
            logging.error(f'Erro na requisição: {response.status_code} - rota: {route}')
            return None

    
    def get_fii_data(self, ticker: str) -> list:
        ''' 
        Obtém os dados de um FII, baseado em seu ticker e fazendo a requisição no Investidor10.
        Transforma valores que representam dados numéricos em float e com pontos e virgulas no estilo EUA.

        Args:
            ticker (str): Ticker do FII que se deseja obter os dados.

        Returns:
            list: Uma lista com os dados do FII.
        '''
        route = ticker.lower()
        soup = self.get_soup_request(route=route)

        data = []
        
        if soup is None:
            return data

        cotacao = soup.find('span', string=f'{ticker.upper()} Cotação')
        cotacao = cotacao.find_next('span').text.strip() if cotacao else 'N/A'
        cotacao = cotacao.replace('R$ ', '').replace(' ', '')
        cotacao = float(cotacao.replace('.', '').replace(',', '.')) if cotacao not in ['-', 'N/A', ''] else 0

        liquidez = soup.find('span', string='Liquidez Diária')
        liquidez = liquidez.find_next('span').text.strip() if liquidez else 'N/A'
        liquidez = liquidez.replace('R$ ', '').replace(' ', '')
        multiplier = 1
        if liquidez.endswith('M'):
            multiplier = 1_000_000
            liquidez = liquidez.replace('M', '')
        elif liquidez.endswith('K'):
            multiplier = 1_000
            liquidez = liquidez.replace('K', '')
        liquidez = float(liquidez.replace(',', '.')) * multiplier if liquidez not in ['-', 'N/A', ''] else 0

        variacao12m = soup.find('span', string='VARIAÇÃO (12M)')
        variacao12m = variacao12m.find_next('span').text.strip() if variacao12m else 'N/A'
        variacao12m = float(variacao12m.replace('%', '').replace(' ', '').replace('.', '').replace(',', '.')) if variacao12m not in ['-', 'N/A', ''] else 0

        cnpj = soup.find('span', string=re.compile(r'CNPJ', re.IGNORECASE))
        cnpj = cnpj.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if cnpj else 'N/A'
        cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '')

        publico_alvo = soup.find('span', string=re.compile(r'PÚBLICO-ALVO', re.IGNORECASE))
        publico_alvo = publico_alvo.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if publico_alvo else 'N/A'
        match publico_alvo:
            case 'fii.QUALIFIED_INVESTOR':
                publico_alvo = 'Investidor Qualificado'
            case 'fii.GENERAL':
                publico_alvo = 'Geral'
            case _:
                pass

        tipo_gestao = soup.find('span', string=re.compile(r'TIPO DE GESTÃO', re.IGNORECASE))
        tipo_gestao = tipo_gestao.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if tipo_gestao else 'N/A'
        match tipo_gestao:
            case 'Passive':
                tipo_gestao = 'Passiva'
            case 'fii.PASSIVE':
                tipo_gestao = 'Passiva'
            case 'Active':
                tipo_gestao = 'Ativa'
            case 'fii.ACTIVE':
                tipo_gestao = 'Ativa'
            case _:
                pass

        taxa_adm = soup.find('span', string=re.compile(r'TAXA DE ADMINISTRAÇÃO', re.IGNORECASE))
        taxa_adm = taxa_adm.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if taxa_adm else 'N/A'

        vacancia = soup.find('span', string=re.compile(r'VACÂNCIA', re.IGNORECASE))
        vacancia = vacancia.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if vacancia else 'N/A'
        vacancia = float(vacancia.replace('%', '').replace(' ', '').replace('.', '').replace(',', '.')) if vacancia not in ['-', 'N/A', ''] else 0

        nro_cotistas = soup.find('span', string=re.compile(r'NUMERO DE COTISTAS', re.IGNORECASE))
        nro_cotistas = nro_cotistas.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if nro_cotistas else 'N/A'
        nro_cotistas = float(nro_cotistas.replace('.', '').replace(' ', '')) if nro_cotistas not in ['-', 'N/A', ''] else 0

        cotas_emitidas = soup.find('span', string=re.compile(r'COTAS EMITIDAS', re.IGNORECASE))
        cotas_emitidas = cotas_emitidas.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if cotas_emitidas else 'N/A'
        cotas_emitidas = float(cotas_emitidas.replace('.', '').replace(' ', '')) if cotas_emitidas not in ['-', 'N/A', ''] else 0

        vl_patrimonial = soup.find('span', string=re.compile(r'VALOR PATRIMONIAL', re.IGNORECASE))
        vl_patrimonial = vl_patrimonial.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if vl_patrimonial else 'N/A'
        vl_patrimonial = vl_patrimonial.replace('Bilhão', 'Bilhões').replace('Milhão', 'Milhões')

        ult_rendimento = soup.find('span', string=re.compile(r'ÚLTIMO RENDIMENTO', re.IGNORECASE))
        ult_rendimento = ult_rendimento.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if ult_rendimento else 'N/A'
        ult_rendimento = ult_rendimento.replace('R$ ', '').replace(' ', '')
        ult_rendimento = float(ult_rendimento.replace('.', '').replace(',', '.')) if ult_rendimento not in ['-', 'N/A', ''] else 0

        data.append([cotacao, liquidez, variacao12m, cnpj, publico_alvo, tipo_gestao, taxa_adm, vacancia, nro_cotistas, cotas_emitidas, vl_patrimonial, ult_rendimento])

        return data[0]


    def get_fiis(self, page: int) -> pd.DataFrame:
        '''
        Obtém os dados dos FIIs de uma determinada página no site Investidor10.
        Transforma valores que representam dados numéricos em float e com pontos e virgulas no estilo EUA.

        Args:
            page (int): A página para se obter os FIIs.

        Returns:
            pd.DataFrame: Um DataFrame contendo os FIIs.
        '''
        route = f'?page={page}'
        soup = self.get_soup_request(route=route)

        columns = ['Ticker', 'Nome', 'P/VP', 'Dividend Yield', 'Tipo', 'Segmento', 'Dados Obtidos', 'Cotação', 
                   'Liquidez Diária', 'Variação 12M', 'CNPJ', 'Público Alvo', 'Tipo de Gestão', 'Taxa de Administração', 
                   'Vacância', 'Número de Cotistas', 'Cotas Emitidas', 'Valor Patrimonial', 'Último Rendimento']

        if soup is None:
            logging.error(f'Erro ao obter dados da página {page}')
            return pd.DataFrame(columns=columns)

        # Find the table containing FII data
        table = soup.find('table', id='rankigns')
        if not table:
            logging.error(f'Tabela não encontrada na página {page}')
            return pd.DataFrame(columns=columns)

        # Find all table rows (skip header row)
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else []

        data = []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 6:  # Ensure we have enough columns
                continue
                
            # Extract ticker and name from the first column (Ativos)
            ativos_cell = cells[0]
            ticker_span = ativos_cell.find('span', class_='font-semibold')
            if not ticker_span:
                continue
            ticker = ticker_span.text.strip()
            
            # Extract name from the second span in the same cell
            nome_spans = ativos_cell.find_all('span')
            nome = 'N/A'
            for span in nome_spans:
                if span.text.strip() != ticker and 'truncate' in span.get('class', []):
                    nome = span.text.strip()
                    break
            
            # Extract Patrimônio Líquido (Net Equity) - column 1
            patrimonio_cell = cells[1]
            patrimonio_div = patrimonio_cell.find('div', class_='money')
            patrimonio_text = patrimonio_div.text.strip() if patrimonio_div else 'N/A'
            
            # Extract Dividend Yield - column 2
            dy_cell = cells[2]
            dy_div = dy_cell.find('div', class_='percent')
            dy_text = dy_div.text.strip() if dy_div else 'N/A'
            dy = float(dy_text.replace('%', '').replace(' ', '').replace('.', '').replace(',', '.')) if dy_text not in ['-', 'N/A', ''] else 0

            # Extract P/VP - column 3
            p_vp_cell = cells[3]
            p_vp_div = p_vp_cell.find('div', class_='decimal')
            p_vp_text = p_vp_div.text.strip() if p_vp_div else 'N/A'
            p_vp = float(p_vp_text.replace('.', '').replace(',', '.')) if p_vp_text not in ['-', 'N/A', ''] else 0

            # Extract Liquidez Diária - column 4
            liquidez_cell = cells[4]
            liquidez_div = liquidez_cell.find('div', class_='money')
            liquidez_text = liquidez_div.text.strip() if liquidez_div else 'N/A'
            liquidez = liquidez_text.replace('R$ ', '').replace(' ', '')
            multiplier = 1
            if liquidez.endswith('M'):
                multiplier = 1_000_000
                liquidez = liquidez.replace('M', '')
            elif liquidez.endswith('K'):
                multiplier = 1_000
                liquidez = liquidez.replace('K', '')
            elif liquidez.endswith('B'):
                multiplier = 1_000_000_000
                liquidez = liquidez.replace('B', '')
            liquidez = float(liquidez.replace(',', '.')) * multiplier if liquidez not in ['-', 'N/A', ''] else 0

            # Extract Variação 12m - column 5
            variacao_cell = cells[5]
            variacao_div = variacao_cell.find('div', class_='var')
            variacao_span = variacao_div.find('span', class_='variation-up') or variacao_div.find('span', class_='variation-down') if variacao_div else None
            variacao_text = variacao_span.text.strip() if variacao_span else 'N/A'
            # Remove arrows and color indicators
            variacao_text = variacao_text.replace('▲', '').replace('▼', '').strip()
            variacao12m = float(variacao_text.replace('%', '').replace(' ', '').replace('.', '').replace(',', '.')) if variacao_text not in ['-', 'N/A', ''] else 0

            # Extract Tipo (Type) - column 6 (hidden but present)
            tipo_cell = cells[6] if len(cells) > 6 else None
            tipo_text = 'N/A'
            if tipo_cell:
                tipo_div = tipo_cell.find('div', class_='text')
                tipo_text = tipo_div.text.strip() if tipo_div else 'N/A'
            
            # Map tipo values
            match tipo_text:
                case 'Fundo de tijolo':
                    tipo = 'Fundo de Tijolo'
                case 'Fundo de papel':
                    tipo = 'Fundo de Papel'
                case 'Fundo de desenvolvimento':
                    tipo = 'Fundo de Desenvolvimento'
                case 'Fundo de fundos':
                    tipo = 'Fundo de Fundos'
                case 'Fundo misto':
                    tipo = 'Fundo Misto'
                case '-':
                    tipo = 'Outro'
                case _:
                    tipo = tipo_text

            # For segmento, we'll set as 'N/A' since it's not visible in the table
            # This would need to be obtained from individual FII pages
            segmento = 'N/A'

            basic_data = [ticker, nome, p_vp, dy, tipo, segmento]

            plus_data = self.get_fii_data(ticker=ticker)
            get_plus_data = True if len(plus_data) != 0 else False
            data.append(basic_data + [get_plus_data] + plus_data)

        for i in range(len(data)):
            if len(data[i]) < len(columns):
                data[i] += [None] * (len(columns) - len(data[i]))

        df = pd.DataFrame(data, columns=columns)

        logging.info(f'Leitura de FIIs da página {page} feita com sucesso! ({len(df)} FIIs obtidos)')
        return df
    

    def get_all_fiis(self) -> pd.DataFrame:
        '''
        Obtém os dados de todos os FIIs do site Investidor10.

        Returns:
            pd.DataFrame: Um DataFrame contendo todos os FIIs do site.
        '''
        all_fiis = pd.DataFrame()
        
        logging.info('Leitura de FIIs do site Investidor10 iniciando...')
        for page in range(1, 16):
            fiis = self.get_fiis(page=page)
            if fiis.empty:
                break
            all_fiis = pd.concat([all_fiis, fiis], ignore_index=True)
        
        all_fiis['Data Atualização'] = datetime.now()

        logging.info('Leitura de FIIs do site Investidor10 concluída!')
        return all_fiis


if __name__ == '__main__':
    FIIsScraper = Investidor10Scraper()
    fiis = FIIsScraper.get_all_fiis()
    
    write_csv_file(data=fiis, file_name=INVESTIDOR10_FILE_NAME)
