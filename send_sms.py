from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

import urllib.parse
import time


class WhatsAppService:

    def __init__(self):

        self.options = Options()

        # Keep WhatsApp logged in
        self.options.add_argument(
            "--user-data-dir=/tmp/chrome-whatsapp-profile"
        )

        # Linux server options
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")

        # Uncomment for headless server
        # self.options.add_argument("--headless=new")

    def send_message(self, phone, message):

        encoded_message = urllib.parse.quote(message)

        url = (
            f"https://web.whatsapp.com/send"
            f"?phone={phone}&text={encoded_message}"
        )

        driver = webdriver.Chrome(options=self.options)

        try:
            driver.get(url)

            # Wait for WhatsApp Web
            time.sleep(20)

            # Press Enter to send
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