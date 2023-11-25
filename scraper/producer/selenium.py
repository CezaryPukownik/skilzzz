import sys
import time
from typing import Any, Generator

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from scraper.logger import logger

from scraper.producer.base import Producer, HTMLResponse


class SeleniumProducer(Producer):
    def __init__(self, address, timeout=60):
        # Connect to remote selenum driver
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")

        for _ in range(timeout):
            try:
                self.webdriver = webdriver.Remote(
                    command_executor=f"http://{address}/wd/hub", options=options
                )
                logger.info("Established connection with remote selenium webdriver")
                break
            except:
                logger.warning(
                    "Unable to connecto to remote driver, retring in 1 second."
                )
                time.sleep(1)
        else:
            raise TimeoutError(
                "Connecting to remote selenium server timeout after {} seconds"
            )

    def render_html(self):
        return HTMLResponse(self.webdriver.page_source)

    def get(self, url, wait_time: int = 0) -> HTMLResponse:
        self.webdriver.get(url)
        if wait_time:
            WebDriverWait(self.webdriver, wait_time)

        return self.render_html()

    def scroll_page(self, scroll_by, wait_time: int = 0) -> None:
        self.webdriver.execute_script(f"window.scrollBy(0, {scroll_by})")
        WebDriverWait(self.webdriver, wait_time)
        return self.render_html()

    def is_page_end(self):
        # Get the current page height
        javascript = """
            const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
            return { scrollTop, scrollHeight, clientHeight };
        """
        scroll_props = self.webdriver.execute_script(javascript)

        # Access the retrieved scroll properties
        scroll_top = scroll_props["scrollTop"]
        scroll_height = scroll_props["scrollHeight"]
        client_height = scroll_props["clientHeight"]

        # Check if the height has changed
        return scroll_top + client_height >= scroll_height

    def get_while_scrolling(
        self, url, wait_time, scroll_by, scroll_wait
    ) -> Generator[HTMLResponse, None, None]:
        # Initial page load and return html
        rendered_html = self.get(url, wait_time=wait_time)
        yield rendered_html

        while not self.is_page_end():
            rendered_html_after_scroll = self.scroll_page(scroll_by=scroll_by, wait_time=scroll_wait)
            if rendered_html_after_scroll != rendered_html:
                rendered_html = rendered_html_after_scroll
                yield rendered_html

    def get_after_scroll(self, url, wait_time, scroll_by, scroll_wait) -> HTMLResponse:
        self.get(url, wait_time=wait_time)
        while not self.is_page_end():
            self.scroll_page(scroll_by=scroll_by, wait_time=scroll_wait)
        
        return self.render_html()

    def on_session_end(self, context):
        self.webdriver.quit()
