import sys
import time
from typing import Any

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from scraper.logger import logger

from scraper.driver.base import Driver


class ChromeSeleniumRemoteDriver(Driver):
   
    def __init__(self, address, timeout=60):
        # Connect to remote selenum driver 
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')

        for _ in range(timeout):
            try:
                self.webdriver = webdriver.Remote(
                    command_executor=f'http://{address}/wd/hub',
                    options=options
                )
                logger.info("Established connection with remote selenium webdriver")
                break
            except:
                logger.warning("Unable to connecto to remote driver, retring in 1 second.")
                time.sleep(1)
        else:
            raise TimeoutError("Connecting to remote selenium server timeout after {} seconds")

    # TODO: What get should result?
    def get(self, url, wait_time: int=0) -> Any:
        self.webdriver.get(url)
        if wait_time:
            WebDriverWait(self.webdriver, wait_time)

        return self.webdriver.page_source

    def render_html(self):
        return self.webdriver.page_source

    def _on_session_end(self, context):
        self.webdriver.quit()
