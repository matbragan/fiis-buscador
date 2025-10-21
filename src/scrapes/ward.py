import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import pandas as pd

# Configurar Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("🔄 Acessando página...")
    driver.get('https://www.ward.app.br/fiis')

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'app-root')))
    time.sleep(5)

    fundos = []
    segmentos = [
        'Logística', 'Logístico', 'Agrícola', 'Lajes Corporativas', 'Shoppings', 'Shopping',
        'Títulos e Val. Mob.', 'Títulos', 'Híbrido', 'Residencial', 'Hospitalar', 'Hotel', 'Hoteleiro',
        'Educacional', 'Industrial', 'Fundos de Fundos', 'Agências', 'Agência', 'Desenvolvimento',
        'Varejo', 'Renda Urbana', 'Outro', 'Outros', 'FIAgro', 'Hedge', 'FoF', 'FI-Infra', 'Cemitério',
        'Papel CRI',
    ]
    segmentos_pattern = '|'.join(segmentos)

    for page in range(1, 36):  # até 35 páginas
        print(f"\n📄 Página {page}...")
        time.sleep(3)

        page_text = driver.find_element(By.TAG_NAME, 'body').text
        lines = page_text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            ticker_match = re.match(r'^([A-Z]{4}\d{2})$', line)
            if ticker_match:
                ticker = ticker_match.group(1)
                segmento = ''
                for j in range(1, min(6, len(lines) - i)):
                    next_line = lines[i + j].strip()
                    seg_match = re.search(f'({segmentos_pattern})', next_line, re.IGNORECASE)
                    if seg_match:
                        segmento = seg_match.group(1)
                        break
                    if re.match(r'^[A-Z]{4}\d{2}$', next_line):
                        break
                if segmento:
                    fundos.append({'Ticker': ticker, 'Segmento': segmento})
            i += 1

        # Ir para a próxima página, se não for a última
        if page < 35:
            try:
                next_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Next' and contains(@class,'page-link')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.8)
                next_button.click()
                print("➡️ Avançando para próxima página...")
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                print("⚠️ Botão '»' não encontrado ou não clicável. Encerrando...")
                break

    if fundos:
        df = pd.DataFrame(fundos).drop_duplicates(subset='Ticker')
        print(f"\n✅ Total de FIIs extraídos: {len(df)}")
        print(df.head())

        df.to_csv('downloads/ward_fiis.csv', index=False, encoding='utf-8-sig')
        print("\n💾 Arquivos salvos com sucesso")
    else:
        print("\n❌ Nenhum FII encontrado.")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n✅ Navegador fechado")
