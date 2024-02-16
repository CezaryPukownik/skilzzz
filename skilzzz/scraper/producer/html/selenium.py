import sys
import time
from typing import Any, Generator

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from scraper.logger import logger

from scraper.producer.html.html import HTMLProducer, HTMLResponse


class SeleniumProducer(HTMLProducer):
    def __init__(self, address, timeout=60, custom_ua=None):
        # Connect to remote selenum driver
        logger.info(f"Connecting to selenium remote driver at {address}")
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")

        if custom_ua:
            options.add_argument(f"user-agent={custom_ua}")


        for _ in range(timeout):
            try:
                self.webdriver = webdriver.Remote(
                    command_executor=f"http://{address}/wd/hub", options=options
                )
                logger.info("Established connection with remote selenium webdriver")
                break
            except:
                logger.warning(
                    "Unable to connect to remote driver, retring in 1 second."
                )
                time.sleep(1)
        else:
            raise TimeoutError(
                "Connecting to remote selenium server timeout after {} seconds"
            )

    def _render_html(self):
        return self.webdriver.page_source

    def get(self, url, wait_time: int = 0) -> HTMLResponse:
        self.webdriver.get(url)
        if wait_time:
            WebDriverWait(self.webdriver, wait_time)

        return HTMLResponse(self._render_html())

    def _scroll_page(self, scroll_by, wait_time: int = 0) -> None:
        logger.info(f"Scrolled page by {scroll_by}, now waiting {wait_time} seconds.")
        self.webdriver.execute_script(f"window.scrollBy(0, {scroll_by})")
        self.webdriver.execute_script(f"await new Promise(r => setTimeout(r, {wait_time}000));")
        return self._render_html()

    def _is_page_end(self):
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
        logger.debug("scroll_top: " + str(scroll_top))
        logger.debug("scroll_height: " + str(scroll_height))
        logger.debug("client_height: " + str(client_height))

        return scroll_top + client_height >= scroll_height

    def get_while_scrolling(
        self, url, wait_time, scroll_by, scroll_wait
    ) -> Generator[HTMLResponse, None, None]:
        # Initial page load and return html
        logger.info("Start scraping scroll down page.")
        self.webdriver.get(url)
        WebDriverWait(self.webdriver, wait_time)
        rendered_html = self._render_html()

        # Return page after initial load
        yield HTMLResponse(rendered_html)
        logger.info("Yielded response.")

        # Scroll down to the end of page and return a page
        # every time html changed.
        while True:
            rendered_html_after_scroll = self._scroll_page(scroll_by=scroll_by, wait_time=scroll_wait)
            if rendered_html_after_scroll != rendered_html:
                rendered_html = rendered_html_after_scroll
                yield HTMLResponse(rendered_html)
                logger.info("Yielded response.")

            if self._is_page_end():
                logger.info("Got to the end of page.")
                break


    def get_after_scroll(self, url, wait_time, scroll_by, scroll_wait) -> HTMLResponse:
        self.get(url, wait_time=wait_time)
        while not self._is_page_end():
            self._scroll_page(scroll_by=scroll_by, wait_time=scroll_wait)
        
        return self._render_html()

    def on_session_end(self):
        logger.info("Scraping session ended. Closing webdriver.")
        self.webdriver.quit()

    def on_session_fail(self):
        logger.error("Scraping session failed. Closing webdriver.")
        self.webdriver.quit()
