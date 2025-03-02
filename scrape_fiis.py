import re
import requests
import pandas as pd
from bs4 import BeautifulSoup


def get_fiis_data(ticker: str) -> list:
    url = f'https://investidor10.com.br/fiis/{ticker.lower()}/'

    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        data = []

        cotacao = soup.find('span', string=f'{ticker.upper()} Cotação')
        cotacao = cotacao.find_next('span').text.strip() if cotacao else 'N/A'

        liquidez = soup.find('span', string='Liquidez Diária')
        liquidez = liquidez.find_next('span').text.strip() if liquidez else 'N/A'

        variacao12m = soup.find('span', string='VARIAÇÃO (12M)')
        variacao12m = variacao12m.find_next('span').text.strip() if variacao12m else 'N/A'

        publico_alvo = soup.find('span', string=re.compile(r'PÚBLICO-ALVO', re.IGNORECASE))
        publico_alvo = publico_alvo.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if publico_alvo else 'N/A'

        tipo_gestao = soup.find('span', string=re.compile(r'TIPO DE GESTÃO', re.IGNORECASE))
        tipo_gestao = tipo_gestao.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if tipo_gestao else 'N/A'

        taxa_adm = soup.find('span', string=re.compile(r'TAXA DE ADMINISTRAÇÃO', re.IGNORECASE))
        taxa_adm = taxa_adm.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if taxa_adm else 'N/A'

        vacancia = soup.find('span', string=re.compile(r'VACÂNCIA', re.IGNORECASE))
        vacancia = vacancia.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if vacancia else 'N/A'

        nro_cotistas = soup.find('span', string=re.compile(r'NUMERO DE COTISTAS', re.IGNORECASE))
        nro_cotistas = nro_cotistas.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if nro_cotistas else 'N/A'

        vl_patrimonial = soup.find('span', string=re.compile(r'VALOR PATRIMONIAL', re.IGNORECASE))
        vl_patrimonial = vl_patrimonial.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if vl_patrimonial else 'N/A'

        ult_rendimento = soup.find('span', string=re.compile(r'ÚLTIMO RENDIMENTO', re.IGNORECASE))
        ult_rendimento = ult_rendimento.find_parent('div', class_='desc').find('div', class_='value').find('span').get_text(strip=True) if ult_rendimento else 'N/A'

        data.append([cotacao, liquidez, variacao12m, publico_alvo, tipo_gestao, taxa_adm, vacancia, nro_cotistas, vl_patrimonial, ult_rendimento])

        return data[0]
    

def get_fiis(page: int) -> pd.DataFrame:
    
    url = f'https://investidor10.com.br/fiis/?page={page}'

    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        fii_cards = soup.find_all('div', class_='actions fii')

        data = []

        for card in fii_cards:
            ticker = card.find('h2', class_='ticker-name').text.strip()
            nome = card.find('h3').text.strip()
            
            p_vp = card.find('span', string='P/VP: ')
            p_vp = p_vp.find_next('span').text.strip() if p_vp else 'N/A'

            dy = card.find('span', string='DY: ')
            dy = dy.find_next('span').text.strip() if dy else 'N/A'

            tipo = card.find('span', string='Tipo: ')
            tipo = tipo.find_next('span').text.strip() if tipo else 'N/A'

            segmento = card.find('span', string='Segmento: ')
            segmento = segmento.find_next('span').text.strip() if segmento else 'N/A'

            plus_data = get_fiis_data(ticker)

            data.append([ticker, nome, p_vp, dy, tipo, segmento] + plus_data)

        df = pd.DataFrame(data, columns=['Ticker', 'Nome', 'P/VP', 'DY', 'Tipo', 'Segmento', 'Cotação', 'Liquidez Diária', 
                                         'Variação 12M', 'Público Alvo', 'Tipo de Gestão', 'Taxa de Administração',
                                         'Vacância', 'Número de Cotistas', 'Valor Patrimonial', 'Último Rendimento'])

        return df

    else:
        print(f'Erro ao acessar a página. Código: {response.status_code}')


def get_all_fiis() -> pd.DataFrame:

    all_fiis = pd.DataFrame()
    
    for page in range(1, 16):
        fiis = get_fiis(page)
        all_fiis = pd.concat([all_fiis, fiis], ignore_index=True)
    
    return all_fiis
