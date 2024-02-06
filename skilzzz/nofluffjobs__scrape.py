from dataclasses import dataclass
from typing import Generator

from scraper.logger import logger
from scraper.output import HTMLOutput, Output
from scraper.producer.html.splash import SplashProducer
from scraper.producer.html.selenium import SeleniumProducer
from scraper.session import Session
from scraper.storer import OverwriteStorer
from scraper.partitioner import YMDTSPartitioner

from scraper.settings import (
    SELENIUM_ADDRESS,
)

@dataclass(frozen=True)
class NofluffSessionSettings:
    url: str

class NofluffjobsSession(Session):

    def process(self) -> Generator[Output, None, None]:
        url = self.settings.url
        page = 1
        next_page = True
        while next_page:
            response = self.producer.get(url, 1)        
            yield HTMLOutput(
                key=f"nofluffjobs-listings-{self.metadata.session_ts}-{page:05}.html",
                content=response, 
            )

            next_page = response.select_one('a[aria-label="Next"]')
            if next_page:
                next_page_url = next_page.get('href')
                logger.info(next_page_url)
                url = f"https://nofluffjobs.com{next_page_url}"
                page += 1

            # yield self.__class__(
            #     producer=SeleniumProducer(address=SELENIUM_ADDRESS),
            #     storer=SimpleStorer(),
            #     settings=NofluffSessionSettings(
            #         url=f"https://nofluffjobs.com{next_page_url}",
            #         wait_time=self.settings.wait_time,
            #         page=self.settings.page+1,
            #     )
            # )
            # Follow link here

        logger.info("Done") 
            
        # if more_offers:
        #     logger.info(f"Scrollable result")
        #     while more_offers:
        #         # Click to load more, wait and scroll down.
        #         logger.info(f"Click & Scroll")
        #         more_offers_btn = producer.webdriver.find_element(
        #             "xpath",
        #             "//*[contains(text(), 'Zobacz więcej ofert')]"
        #         ).click()
        #         producer.webdriver.implicitly_wait(5)

        #         # while not self._is_page_end():
        #         #     self._scroll_page(scroll_by=100, wait_time=1)
                
        #         # Get response after scrolling
        #         response = HTMLResponse(self._render_html())
        #         more_offers = get_scroll_button(response)
            
        #     logger.info(f"Out of scroll button. Ending.")
        #     yield TextOutput(
        #         response.html.prettify(), 
        #         f"nofulljobs/lists/{self.metadata.session_id}.html"
        #     )


if __name__ == "__main__":
    session = NofluffjobsSession(
        name='nofluffjobs',
        collection='offerlist',
        producer=SeleniumProducer(
            address=SELENIUM_ADDRESS,
            custom_ua="Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ),
        # producer=SplashProducer(host="0.0.0.0", port="8050"),
        storer=OverwriteStorer(storage='fs'),
        settings=NofluffSessionSettings(
            url = "https://nofluffjobs.com/pl/data",
        )
    )
    session.start()