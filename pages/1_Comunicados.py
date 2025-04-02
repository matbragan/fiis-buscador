import pandas as pd

from fiis.constants import MY_FIIS
from fiis.scrapes.investidor10 import Investidor10Scraper


scrape = Investidor10Scraper()

for ticker in MY_FIIS:
    soup_request = scrape.get_soup_request(route=ticker.lower())

    communications_section = soup_request.find('section', id='communications-section')
    communications = communications_section.find_all('div', class_='communication-card')

    communications_list = [
        {
            'Ticker': ticker.upper(),
            'Comunicado': comm.find('p', class_='communication-card--content').text.strip(),
            'Data Comunicado': comm.find('span', class_='card-date--content').text.strip(),
            'Link': comm.find('a', class_='btn-download-communication')['href']
        }
        for comm in communications
    ]

    communications_df = pd.DataFrame(communications_list)

    communications_df
