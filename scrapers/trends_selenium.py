# scrapers/trends_selenium.py
"""
Selenium Google Trends snapshot using modern Selenium initialization.
Saves HTML to outputs/trends_selenium_sample.html
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

OUT = os.path.join(os.path.dirname(__file__), "../outputs")
os.makedirs(OUT, exist_ok=True)

KEYWORD = "texture painting"

def run_trends_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Modern Selenium initialization
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        url = f"https://trends.google.com/trends/explore?q={KEYWORD.replace(' ','%20')}"
        print("[Selenium] Opening:", url)
        driver.get(url)

        time.sleep(5)  # allow JS to load

        html = driver.page_source
        save_path = os.path.join(OUT, "trends_selenium_sample.html")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html)

        print("[Selenium] Saved HTML snapshot to:", save_path)
    except Exception as e:
        print("[Selenium] Error:", e)
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    run_trends_selenium()
