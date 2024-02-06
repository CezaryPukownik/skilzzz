from dataclasses import dataclass
from collections import namedtuple
import json
from pathlib import Path
from datetime import datetime
from typing import Generator
from urllib.parse import urljoin

import click

from scraper.logger import logger
from scraper.output import HTMLOutput, Output
from scraper.session import Session
from scraper.storer import OverwriteStorer
from scraper.producer.html.selenium import SeleniumProducer
from scraper.stepfunctions import stepfunctions_callback_handler

from scraper.settings import SELENIUM_ADDRESS


@dataclass(frozen=True)
class JustjoinitOffersScraperSettings:
    url: str
    init_wait: int
    scroll_wait: int
    scroll_by: int


class JustjoinitOffersScraper(Session):

    def process(self) -> Generator[HTMLOutput|Session, None, None]:

        # This should not be settings of a session
        # but arguments of process function... 
        # implement Dagster-style?

        url = self.settings.url
        init_wait = self.settings.init_wait
        scroll_wait = self.settings.scroll_wait
        scroll_by = self.settings.scroll_by
        producer = self.producer

        followed_links = []
        for i, response in enumerate(
            producer.get_while_scrolling(
                url, wait_time=init_wait, scroll_wait=scroll_wait, scroll_by=scroll_by
            )
        ):
            # Save each response
            yield HTMLOutput(
                key=f"justjoinit-listings-{self.metadata.session_ts}-{i:05}.html",
                content=response
            )

            # parse every offer from response
            offers = response.select("[data-index]")
            for offer in offers:
                offer_index = int(offer.get("data-index"))
                offer_link = offer.select_one("a").get("href")

                follow_link = urljoin("https://justjoin.it/", offer_link)
                if follow_link not in followed_links:
                    logger.info(
                        f"Rendered page: {i}, offer data-index {offer_index}: {follow_link}"
                    )

                    # Spawn new session
                    yield JustjoinitOfferPageScraper(
                        name='justjoinit',
                        collection='offers',
                        producer=SeleniumProducer(address=SELENIUM_ADDRESS),
                        storer=OverwriteStorer(storage='fs'),
                        settings=JustjoinitOfferPageScraperSettings(
                            url=follow_link,
                            offer_index=offer_index,
                        ),
                    )

                # Remember followed links to prevent from scraping duplicates.
                followed_links.append(follow_link)


@dataclass(frozen=True)
class JustjoinitOfferPageScraperSettings:
    url: str 
    offer_index: int

class JustjoinitOfferPageScraper(Session):
    def process(self) -> Generator[Output, None, None]:
        response = self.producer.get(self.settings.url, wait_time=1)
        offer_id = self.settings.url.split("/")[-1]
        yield HTMLOutput(
            key=f"{self.settings.offer_index:05}-{offer_id}.html",
            content=response,
        )

@click.command()
@click.option("--init-wait", default=3, type=int, help="Seconds await until page loads")
@click.option("--scroll-wait", default=1, type=int, help="Seconds wait after scrolling down")
@click.option("--scroll-by", default=500, type=int, help="Pixels of each scroll down action")
@stepfunctions_callback_handler
def main(init_wait, scroll_wait, scroll_by):
    assets = JustjoinitOffersScraper(
        name='justjoinit',
        collection='offerlist',
        producer=SeleniumProducer(address=SELENIUM_ADDRESS),
        storer=OverwriteStorer(storage='fs'),
        settings=JustjoinitOffersScraperSettings(
            url="https://justjoin.it/all-locations/data",
            init_wait=3,
            scroll_wait=3,
            scroll_by=500,
        ),
    ).start()

    logger.info("Session output:\n" + json.dumps(assets, indent=4))
    return assets

if __name__ == "__main__":
    main()
