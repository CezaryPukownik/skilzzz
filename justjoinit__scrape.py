from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import time
from typing import Generator

from threading import Thread
from functools import partialmethod

from bs4 import BeautifulSoup

from scraper.logger import logger
from scraper.output import FileOutput, Output
from scraper.session import Session
from scraper.storer import FileSystemStorer, PartitionedFileSystemStorer, PartitionedS3FileStorer
from scraper.partitioner import YMDPartitioner
from scraper.driver.chrome_selenium_remote import ChromeSeleniumRemoteDriver

from scraper.settings import  (
    SELENIUM_ADDRESS, 
    S3_BUCKET,
    JUSTJOINIT_HTML_LISTING_PATH,
    JUSTJOINIT_HTML_OFFERS_PATH,
)

@dataclass(frozen=True)
class JustjoinitContext:
    url: str
    init_sleep: int
    scroll_interval: int
    scroll_by: int

class JustjoinitSession(Session):
   
    def generate_outputs(self, driver, context: JustjoinitContext) -> Generator[FileOutput, None, None]:
        html = None
        url = context.url
        init_sleep = context.init_sleep
        scroll_interval = context.scroll_interval
        scroll_by = context.scroll_by

        threads=[]
        followed_links = []
        current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        logger.info(f"Openning url {url}...")
        driver.get(url)

        logger.info(f"Waiting for {init_sleep} seconds...")
        time.sleep(init_sleep)

        logger.info("Started scrolling")
        i = 0
        while True:
            driver.webdriver.execute_script(f"""window.scrollBy(0, {scroll_by})""")
            time.sleep(scroll_interval) # seconds

            # Get the current page height
            javascript = """
                const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
                return { scrollTop, scrollHeight, clientHeight };
            """
            scroll_props = driver.webdriver.execute_script(javascript)

            # Access the retrieved scroll properties
            scroll_top = scroll_props['scrollTop']
            scroll_height = scroll_props['scrollHeight']
            client_height = scroll_props['clientHeight']

            # Check if the height has changed
            if scroll_top+client_height >= scroll_height:
                break

            logger.info(f"Current position: {scroll_top+client_height}, Page size: {scroll_height}, Page index: {i}")

            # Return rendered HTML if html was updated.
            if html != driver.webdriver.page_source:
                html = driver.webdriver.page_source

                filename = Path(f"{current_timestamp}-{i:05}.html")
                yield FileOutput(content=html, filename=filename)
                i += 1
            
                # Parse each order as separate session. 
                soup = BeautifulSoup(html, 'html.parser')
                offers = soup.select("[data-index]")
                for offer in offers:
                    follow_link = offer.select_one('a').get('href')
                    offer_index = int(offer.get('data-index'))
                    if follow_link not in followed_links:
                        logger.info(f"Following offer {i}, data-index {offer_index}: {follow_link}")

                        # Spawn new session
                        s3_storer = PartitionedS3FileStorer(
                            bucket=S3_BUCKET, 
                            prefix=JUSTJOINIT_HTML_OFFERS_PATH, 
                            partitioner=YMDPartitioner(after={"ts": current_timestamp})
                        )
                        page_session = JustjoinitOfferPageSession(
                            driver=ChromeSeleniumRemoteDriver(address=SELENIUM_ADDRESS),
                            storer=s3_storer
                        )
                            
                        page_context = JustjoinitOfferPageContext(follow_link=follow_link, offer_index=offer_index)
                        thread = Thread(target=page_session.start, args=(page_context,))
                        thread.start()

                        # Remembed followed links to prevent from scraping duplicates.
                        followed_links.append(follow_link)

        logger.info("Got to the end of page.")


@dataclass(frozen=True)
class JustjoinitOfferPageContext:
    follow_link: str
    offer_index: int

class JustjoinitOfferPageSession(Session):
    
    def generate_outputs(self, driver, context: JustjoinitOfferPageContext) -> Generator[Output, None, None]:
        base_url = "https://justjoin.it"
        url = base_url + context.follow_link
        offer_id = context.follow_link.split("/")[-1]
        filename = f"{context.offer_index:05}-{offer_id}.html"
        yield FileOutput(
            content=driver.get(url),
            filename=filename
        )


if __name__ == "__main__":

    session_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    s3_storer = PartitionedS3FileStorer(
        bucket=S3_BUCKET, 
        prefix=JUSTJOINIT_HTML_LISTING_PATH, 
        partitioner=YMDPartitioner(after={"ts": session_timestamp})
    )

    session = JustjoinitSession(
        driver=ChromeSeleniumRemoteDriver(address=SELENIUM_ADDRESS),
        storer=s3_storer
    )

    url = "https://justjoin.it/all-locations/data"

    context = JustjoinitContext(
        url=url, init_sleep=5, scroll_by=100, scroll_interval=0.2
    )

    session.start(context)