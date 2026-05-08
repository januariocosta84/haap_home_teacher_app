from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import urllib.parse
import time


class WhatsAppService:

    def __init__(self):

        self.options = Options()

        options = Options()
        options.binary_location = "/usr/bin/google-chrome"

        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        service = Service("/usr/bin/chromedriver")

        driver = webdriver.Chrome(service=service, options=options)


    def start_browser(self):

        service = Service("/usr/bin/chromedriver")

        driver = webdriver.Chrome(
            service=service,
            options=self.options
        )

        return driver

    def send_message(self, phone, message):

        driver = self.start_browser()

        try:

            encoded_message = urllib.parse.quote(message)

            url = (
                f"https://web.whatsapp.com/send"
                f"?phone={phone}&text={encoded_message}"
            )

            driver.get(url)

            # Wait WhatsApp load
            time.sleep(20)

            # Press ENTER to send
            input_box = driver.find_element(
                By.XPATH,
                '//div[@contenteditable="true"][@data-tab="10"]'
            )

            input_box.send_keys(Keys.ENTER)

            time.sleep(5)

            return True

        except Exception as e:

            print("WhatsApp Error:", e)

            return False

        finally:

            driver.quit()