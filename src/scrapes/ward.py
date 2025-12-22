import logging
import re
import time

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import WARD_FILE
from src.utils import write_csv_file

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


def get_ward_fiis() -> pd.DataFrame:
    """
    Obtém os dados de FIIs do site Ward.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs do site Ward.
    """
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)

    try:
        logging.info("Leitura de FIIs do site Ward iniciando...")
        driver.get("https://www.ward.app.br/fiis")

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "app-root")))
        time.sleep(5)

        fundos = []
        segmentos = [
            "Logística",
            "Logístico",
            "Agrícola",
            "Lajes Corporativas",
            "Shoppings",
            "Shopping",
            "Títulos e Val. Mob.",
            "Títulos",
            "Híbrido",
            "Residencial",
            "Hospitalar",
            "Hotel",
            "Hoteleiro",
            "Educacional",
            "Industrial",
            "Fundos de Fundos",
            "Agências",
            "Agência",
            "Desenvolvimento",
            "Varejo",
            "Renda Urbana",
            "Outro",
            "Outros",
            "FIAgro",
            "Hedge",
            "FoF",
            "FI-Infra",
            "Cemitério",
            "Papel CRI",
        ]
        segmentos_pattern = "|".join(segmentos)

        for page in range(1, 36):
            time.sleep(0.8)

            page_text = driver.find_element(By.TAG_NAME, "body").text
            lines = page_text.split("\n")

            i = 0
            while i < len(lines):
                line = lines[i].strip()
                ticker_match = re.match(r"^([A-Z]{4}\d{2})$", line)
                if ticker_match:
                    ticker = ticker_match.group(1)
                    segmento = ""
                    for j in range(1, min(6, len(lines) - i)):
                        next_line = lines[i + j].strip()
                        seg_match = re.search(f"({segmentos_pattern})", next_line, re.IGNORECASE)
                        if seg_match:
                            segmento = seg_match.group(1)
                            break
                        if re.match(r"^[A-Z]{4}\d{2}$", next_line):
                            break
                    if segmento:
                        fundos.append({"Ticker": ticker, "Segmento": segmento})
                i += 1

            # Log progress apenas a cada 5 páginas ou na última página
            if page % 5 == 0:
                logging.info(
                    f"Processando página {page}/35... ({len(fundos)} FIIs encontrados até agora)"
                )

            # Ir para a próxima página, se não for a última
            if page < 35:
                try:
                    # Tentar múltiplos seletores para encontrar o botão "Next"
                    next_button = None
                    selectors = [
                        (By.XPATH, "//a[@aria-label='Next' and contains(@class,'page-link')]"),
                        (By.XPATH, "//a[contains(@aria-label,'Next')]"),
                        (By.XPATH, "//a[contains(@class,'page-link') and contains(text(),'»')]"),
                        (By.XPATH, "//a[contains(@class,'page-link') and @aria-label='Next']"),
                        (By.CSS_SELECTOR, "a.page-link[aria-label='Next']"),
                        (By.CSS_SELECTOR, "a[aria-label='Next']"),
                    ]

                    for selector_type, selector_value in selectors:
                        try:
                            next_button = wait.until(
                                EC.presence_of_element_located((selector_type, selector_value))
                            )
                            # Verificar se o botão está visível e habilitado
                            if next_button.is_displayed() and next_button.is_enabled():
                                # Verificar se não está desabilitado pela classe
                                classes = next_button.get_attribute("class") or ""
                                if "disabled" not in classes.lower():
                                    break
                        except (TimeoutException, NoSuchElementException):
                            continue

                    if next_button is None:
                        raise NoSuchElementException("Botão Next não encontrado com nenhum seletor")

                    # Scroll até o botão
                    driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                        next_button,
                    )
                    time.sleep(1)

                    # Tentar clicar normalmente primeiro
                    try:
                        next_button.click()
                    except ElementClickInterceptedException:
                        # Se o clique normal falhar, usar JavaScript (sem log, é comportamento esperado)
                        driver.execute_script("arguments[0].click();", next_button)

                    # Aguardar a página carregar
                    time.sleep(1.5)

                except (TimeoutException, NoSuchElementException) as e:
                    logging.warning(
                        f'Botão "Next" não encontrado na página {page}. Encerrando... Erro: {e}'
                    )
                    break
                except ElementClickInterceptedException as e:
                    logging.warning(
                        f'Botão "Next" interceptado na página {page}. Tentando JavaScript... Erro: {e}'
                    )
                    try:
                        driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(1.5)
                    except Exception as e2:
                        logging.warning(
                            f"Falha ao clicar no botão mesmo com JavaScript. Encerrando... Erro: {e2}"
                        )
                        break
                except Exception as e:
                    logging.warning(
                        f"Erro inesperado ao tentar avançar página {page}. Encerrando... Erro: {e}"
                    )
                    break

        if fundos:
            df = pd.DataFrame(fundos).drop_duplicates(subset="Ticker")
            df["Segmento"] = df["Segmento"].str.title()
            replacements = {
                "Logístico": "Logística",
                "Papel Cri": "Papel CRI",
                "Fiagro": "FIAgro",
                "Fi-Infra": "FI-Infra",
                "Fof": "FoF",
                "Shopping": "Shoppings",
                "Agências": "Agências Bancárias",
            }
            df["Segmento"] = df["Segmento"].replace(replacements)
            logging.info(f"Total de FIIs extraídos: {len(df)}")

            return df
        else:
            logging.warning("Nenhum FII encontrado.")

    except Exception as e:
        logging.error(f"Erro: {e}")
        import traceback

        traceback.print_exc()

    finally:
        driver.quit()


if __name__ == "__main__":
    fiis = get_ward_fiis()
    write_csv_file(data=fiis, file_path=WARD_FILE)
