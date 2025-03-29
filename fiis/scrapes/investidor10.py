import os
import re
import sys
import logging
from datetime import datetime

import requests
import pandas as pd
from bs4 import BeautifulSoup

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from fiis.constants import INVESTIDOR10_BASE_URL, HEADERS, INVESTIDOR10_FILE_NAME
from fiis.utils import write_csv_file


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
            logging.error(f'Erro na requisição: {response.status_code}')
            exit(1)

    
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
            case 'Active':
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

        vl_patrimonial = soup.find('span', string=re.compile(r'VALOR PATRIMONIAL', re.IGNORECASE))
        vl_patrimonial = vl_patrimonial.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if vl_patrimonial else 'N/A'
        vl_patrimonial = vl_patrimonial.replace('Bilhão', 'Bilhões').replace('Milhão', 'Milhões')

        ult_rendimento = soup.find('span', string=re.compile(r'ÚLTIMO RENDIMENTO', re.IGNORECASE))
        ult_rendimento = ult_rendimento.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if ult_rendimento else 'N/A'
        ult_rendimento = ult_rendimento.replace('R$ ', '').replace(' ', '')
        ult_rendimento = float(ult_rendimento.replace('.', '').replace(',', '.')) if ult_rendimento not in ['-', 'N/A', ''] else 0

        data.append([cotacao, liquidez, variacao12m, publico_alvo, tipo_gestao, taxa_adm, vacancia, nro_cotistas, vl_patrimonial, ult_rendimento])

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

        fii_cards = soup.find_all('div', class_='actions fii')

        data = []
        
        for card in fii_cards:
            ticker = card.find('h2', class_='ticker-name').text.strip()
            nome = card.find('h3').text.strip()
            
            p_vp = card.find('span', string='P/VP: ')
            p_vp = p_vp.find_next('span').text.strip() if p_vp else 'N/A'
            p_vp = float(p_vp.replace('.', '').replace(',', '.')) if p_vp not in ['-', 'N/A', ''] else 0

            dy = card.find('span', string='DY: ')
            dy = dy.find_next('span').text.strip() if dy else 'N/A'
            dy = float(dy.replace('%', '').replace(' ', '').replace('.', '').replace(',', '.')) if dy not in ['-', 'N/A', ''] else 0

            tipo = card.find('span', string='Tipo: ')
            tipo = tipo.find_next('span').text.strip() if tipo else 'N/A'
            match tipo:
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
                    pass

            segmento = card.find('span', string='Segmento: ')
            segmento = segmento.find_next('span').text.strip() if segmento else 'N/A'
            match segmento:
                case 'Logístico / Indústria / Galpões':
                    segmento = 'Logístico'
                case 'Shoppings / Varejo':
                    segmento = 'Shoppings'
                case 'Títulos e Valores Mobiliários':
                    segmento = 'Títulos e Val. Mob.'
                case _:
                    pass

            basic_data = [ticker, nome, p_vp, dy, tipo, segmento]

            plus_data = self.get_fii_data(ticker=ticker)
            data.append(basic_data + plus_data)

        columns = ['Ticker', 'Nome', 'P/VP', 'Dividend Yield', 'Tipo', 'Segmento', 'Cotação', 
                   'Liquidez Diária', 'Variação 12M', 'Público Alvo', 'Tipo de Gestão', 'Taxa de Administração', 
                   'Vacância', 'Número de Cotistas', 'Valor Patrimonial', 'Último Rendimento']

        df = pd.DataFrame(data, columns=columns)

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
            logging.info(f'Leitura de FIIs da página {page} feita com sucesso!')
            all_fiis = pd.concat([all_fiis, fiis], ignore_index=True)
        
        all_fiis['Data Atualização'] = datetime.now()

        logging.info('Todos FIIs obtidos com sucesso!')
        return all_fiis


if __name__ == '__main__':
    FIIsScraper = Investidor10Scraper()
    fiis = FIIsScraper.get_all_fiis()
    
    write_csv_file(data=fiis, file_name=INVESTIDOR10_FILE_NAME)
