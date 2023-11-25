from bs4 import BeautifulSoup
from pathlib import Path

from scraper.logger import logger
from scraper.output import FileOutput, Output
from scraper.session import Session
from scraper.storer import LocalFileStorer, PartitionedFileSystemStorer, PartitionedS3FileStorer
from scraper.partitioner import YMDPartitioner
from scraper.producer.selenium import SeleniumProducer

from scraper.settings import (
    SELENIUM_ADDRESS,
    S3_BUCKET,
    JUSTJOINIT_HTML_LISTING_PATH,
    JUSTJOINIT_HTML_OFFERS_PATH,
    TIMESTAMP_FORMAT,
)


class NofluffjobsSession(Session):

    def process(self, driver, context) -> Generator[Output, None, None]:
        start_url = "https://nofluffjobs.com/pl/data?page=1"
        page = 1

        html = driver.get(start_url, 5)
        driver.webdriver.set_window_size(1920, 1080)
        yield FileOutput(html, Path(f"nofulljobs/lists/page_{page}.html"))

        soup = BeautifulSoup(html, 'html.parser')


if __name__ == "__main__":
    driver = SeleniumProducer(address=SELENIUM_ADDRESS)
    session = NofluffjobsSession(producer=driver, storer=LocalFileStorer())
