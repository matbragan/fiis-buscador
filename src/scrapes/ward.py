"""
Scraper para obter dados dos FIIs do site Ward.
"""

import logging
import re
import time
import traceback
from typing import Dict, List, Optional

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

from config.settings import WARD_BASE_URL, WARD_FILE
from src.utils.write_files import write_csv_file

log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


def get_segmentos_list() -> List[str]:
    """
    Retorna a lista de segmentos de FIIs para busca.

    Returns:
        List[str]: Lista de segmentos.
    """
    return [
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


def setup_chrome_driver() -> webdriver.Chrome:
    """
    Configura e retorna uma instância do Chrome driver.

    Returns:
        webdriver.Chrome: Instância configurada do Chrome driver.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=chrome_options)


def navigate_to_ward_page(driver: webdriver.Chrome) -> WebDriverWait:
    """
    Navega para a página inicial do Ward e aguarda o carregamento.

    Args:
        driver: Instância do Chrome driver.

    Returns:
        WebDriverWait: Instância do WebDriverWait configurada.
    """
    logging.info("Leitura de FIIs do site Ward iniciando...")
    driver.get(WARD_BASE_URL)

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "app-root")))
    time.sleep(0.8)

    return wait


def extract_funds_from_page(
    driver: webdriver.Chrome, segmentos_pattern: str
) -> List[Dict[str, str]]:
    """
    Extrai os dados dos fundos da página atual.

    Args:
        driver: Instância do Chrome driver.
        segmentos_pattern: Padrão regex com os segmentos para busca.

    Returns:
        List[Dict[str, str]]: Lista de dicionários com Ticker e Segmento.
    """
    fundos = []
    page_text = driver.find_element(By.TAG_NAME, "body").text
    lines = page_text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        ticker_match = re.match(r"^([A-Z]{4}\d{2})$", line)
        if ticker_match:
            ticker = ticker_match.group(1)
            segmento = _find_segmento_for_ticker(lines, i, segmentos_pattern)
            if segmento:
                fundos.append({"Ticker": ticker, "Segmento": segmento})
        i += 1

    return fundos


def _find_segmento_for_ticker(lines: List[str], ticker_index: int, segmentos_pattern: str) -> str:
    """
    Encontra o segmento para um ticker específico nas linhas seguintes.

    Args:
        lines: Lista de linhas do texto da página.
        ticker_index: Índice da linha onde o ticker foi encontrado.
        segmentos_pattern: Padrão regex com os segmentos.

    Returns:
        str: Segmento encontrado ou string vazia.
    """
    for j in range(1, min(6, len(lines) - ticker_index)):
        next_line = lines[ticker_index + j].strip()
        seg_match = re.search(f"({segmentos_pattern})", next_line, re.IGNORECASE)
        if seg_match:
            return seg_match.group(1)
        if re.match(r"^[A-Z]{4}\d{2}$", next_line):
            break
    return ""


def find_next_button(wait: WebDriverWait) -> Optional[webdriver.remote.webelement.WebElement]:
    """
    Encontra o botão de próxima página usando múltiplos seletores.

    Args:
        driver: Instância do Chrome driver.
        wait: Instância do WebDriverWait.

    Returns:
        Optional[WebElement]: Elemento do botão Next ou None se não encontrado.
    """
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
            if next_button.is_displayed() and next_button.is_enabled():
                classes = next_button.get_attribute("class") or ""
                if "disabled" not in classes.lower():
                    return next_button
        except (TimeoutException, NoSuchElementException):
            continue

    return None


def click_next_button(
    driver: webdriver.Chrome, next_button: webdriver.remote.webelement.WebElement
) -> None:
    """
    Clica no botão de próxima página, usando JavaScript se necessário.

    Args:
        driver: Instância do Chrome driver.
        next_button: Elemento do botão Next.
    """
    driver.execute_script(
        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
        next_button,
    )
    time.sleep(1)

    try:
        next_button.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", next_button)

    time.sleep(1)


def navigate_to_next_page(driver: webdriver.Chrome, wait: WebDriverWait, page: int) -> bool:
    """
    Navega para a próxima página.

    Args:
        driver: Instância do Chrome driver.
        wait: Instância do WebDriverWait.
        page: Número da página atual.

    Returns:
        bool: True se conseguiu navegar, False caso contrário.
    """
    try:
        next_button = find_next_button(wait)
        if next_button is None:
            raise NoSuchElementException("Botão Next não encontrado com nenhum seletor")

        click_next_button(driver, next_button)
        return True

    except (TimeoutException, NoSuchElementException) as e:
        logging.warning(f'Botão "Next" não encontrado na página {page}. Encerrando... Erro: {e}')
        return False
    except ElementClickInterceptedException as e:
        logging.warning(
            f'Botão "Next" interceptado na página {page}. Tentando JavaScript... Erro: {e}'
        )
        try:
            next_button = find_next_button(wait)
            if next_button:
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(1)
                return True
        except Exception as e2:
            logging.warning(
                f"Falha ao clicar no botão mesmo com JavaScript. Encerrando... Erro: {e2}"
            )
        return False
    except Exception as e:
        logging.warning(f"Erro inesperado ao tentar avançar página {page}. Encerrando... Erro: {e}")
        return False


def process_funds_data(fundos: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Processa e limpa os dados dos fundos extraídos.

    Args:
        fundos: Lista de dicionários com dados dos fundos.

    Returns:
        pd.DataFrame: DataFrame processado com os dados dos fundos.
    """
    if not fundos:
        logging.error("Nenhum FII encontrado.")
        raise Exception("Nenhum FII encontrado.")

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
    logging.info(f"✓ Total de FIIs extraídos: {len(df)}")

    return df


def main() -> pd.DataFrame:
    """
    Obtém os dados de FIIs do site Ward.

    Returns:
        pd.DataFrame: Um DataFrame contendo os dados dos FIIs do site Ward.
    """
    driver = setup_chrome_driver()

    try:
        wait = navigate_to_ward_page(driver)

        fundos = []
        segmentos = get_segmentos_list()
        segmentos_pattern = "|".join(segmentos)

        # Aguarda um tempo adicional para garantir que a primeira página carregou completamente
        time.sleep(2)

        for page in range(1, 36):
            time.sleep(0.8)

            page_fundos = extract_funds_from_page(driver, segmentos_pattern)
            fundos.extend(page_fundos)

            if page % 5 == 0:
                logging.info(
                    f"Processando página {page}/35... ({len(fundos)} FIIs encontrados até agora)"
                )

            if page < 35:
                if not navigate_to_next_page(driver, wait, page):
                    break

        return process_funds_data(fundos)

    except Exception as e:
        logging.error(f"Erro: {e}")
        traceback.print_exc()
        raise Exception(f"Erro ao obter dados dos FIIs do site Ward: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    fiis = main()
    write_csv_file(data=fiis, file_path=WARD_FILE)
