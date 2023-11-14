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
from scraper.storer import FileSystemStorer, PartitionedFileSystemStorer
from scraper.partitioner import YMDPartitioner
from scraper.driver.chrome_selenium_remote import ChromeSeleniumRemoteDriver

from scraper.settings import SELENIUM_ADDRESS, JUSTJOINIT_STORAGE_PATH, JUSTJOINIT_PAGES_PATH

@dataclass(frozen=True)
class JustjoinitContext:
    url: str
    init_sleep: int
    scroll_interval: int
    scroll_by: int

class JustjoinitSession(Session):
   
    def generate_outputs(self, driver, context: JustjoinitContext) -> Generator[FileOutput, None, None]:
        try:
            threads = []
            html = None
            url = context.url
            init_sleep = context.init_sleep
            scroll_interval = context.scroll_interval
            scroll_by = context.scroll_by
            
            followed_links = []
            current_timestamp = datetime.now().strftime("%y%m%d%H%M%S")

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
                            page_session = JustjoinitOfferPageSession(
                                driver=ChromeSeleniumRemoteDriver(address=SELENIUM_ADDRESS),
                                storer=PartitionedFileSystemStorer(
                                    path=JUSTJOINIT_PAGES_PATH, 
                                    partitioner=YMDPartitioner(after={'ts': current_timestamp})
                                )
                            )
                                
                            page_context = JustjoinitOfferPageContext(follow_link=follow_link, offer_index=offer_index)
                            thread = Thread(target=page_session.start, args=(page_context,))
                            threads.append(thread)
                            thread.start()

                            # Remembed followed links to prevent from scraping duplicates.
                            followed_links.append(follow_link)

            logger.info("Got to the end of page.")
            for thread in threads:
                thread.join()

        except Exception as e:
            raise e

        finally:
            # Close the ChromeDriver instance
            self.driver.webdriver.quit()

@dataclass(frozen=True)
class JustjoinitOfferPageContext:
    follow_link: str
    offer_index: int

class JustjoinitOfferPageSession(Session):
    
    def generate_outputs(self, driver, context: JustjoinitOfferPageContext) -> Generator[Output, None, None]:
        try:
            base_url = "https://justjoin.it"
            url = base_url + context.follow_link
            offer_id = context.follow_link.split("/")[-1]
            filename = f"{context.offer_index:05}-{offer_id}.html"
            yield FileOutput(
                content=driver.get(url),
                filename=filename
            )

        except Exception as e:
            logger.error(e)
            raise e
    
        finally:
            driver.webdriver.quit()
        

if __name__ == "__main__":

    current_timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    session = JustjoinitSession(
        driver=ChromeSeleniumRemoteDriver(address=SELENIUM_ADDRESS),
        storer=PartitionedFileSystemStorer(path=JUSTJOINIT_STORAGE_PATH, partitioner=YMDPartitioner(after={"ts": current_timestamp}))
    )
    url = "https://justjoin.it/all-locations/data"

    context = JustjoinitContext(
        url=url, init_sleep=5, scroll_by=100, scroll_interval=0.2
    )

    session.start(context)