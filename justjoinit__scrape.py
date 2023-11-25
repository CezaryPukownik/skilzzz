from dataclasses import dataclass
from pathlib import Path
from typing import Generator
from urllib.parse import urljoin

from scraper.logger import logger
from scraper.output import FileOutput, Output
from scraper.producer.base import HTMLResponse
from scraper.session import Session
from scraper.storer import S3FileStorer
from scraper.partitioner import YMDPartitioner
from scraper.producer.selenium import SeleniumProducer
from scraper.stepfunctions import task

from scraper.settings import (
    SELENIUM_ADDRESS,
    S3_BUCKET,
    JUSTJOINIT_HTML_LISTING_PATH,
    JUSTJOINIT_HTML_OFFERS_PATH,
    TIMESTAMP_FORMAT,
)


@dataclass(frozen=True)
class JustjoinitSessionSettings:
    url: str
    init_wait: int
    scroll_wait: int
    scroll_by: int
    session_timestamp: str


class JustjoinitSession(Session):
    def listing_output(self, i: int, response: HTMLResponse):
        partition = YMDPartitioner(date=self.metadata.started_at).get()
        current_timestamp = self.metadata.started_at.strftime(TIMESTAMP_FORMAT)
        filename = Path(f"justjoinit-listings-{current_timestamp}-{i:05}.html")
        return FileOutput(
            content=response.html,
            filename=JUSTJOINIT_HTML_LISTING_PATH / partition / filename,
        )

    def process(
        self, producer: SeleniumProducer, settings: JustjoinitSessionSettings
    ) -> Generator[FileOutput, None, None]:
        url = settings.url
        init_wait = settings.init_wait
        scroll_wait = settings.scroll_wait
        scroll_by = settings.scroll_by

        followed_links = []
        for i, response in enumerate(
            producer.get_while_scrolling(
                url, wait_time=init_wait, scroll_wait=scroll_wait, scroll_by=scroll_by
            )
        ):
            # Save each response
            yield self.listing_output(i, response)

            # parse every offer from response
            offers = response.select("[data-index]")
            for offer in offers:
                follow_link = offer.select_one("a").get("href")
                offer_index = int(offer.get("data-index"))
                if follow_link not in followed_links:
                    logger.info(
                        f"Following offer {i}, data-index {offer_index}: {follow_link}"
                    )

                    # Spawn new session
                    yield JustjoinitOfferPageSession(
                        producer=SeleniumProducer(address=SELENIUM_ADDRESS),
                        storer=S3FileStorer(bucket=S3_BUCKET),
                        settings=JustjoinitOfferPageSessionSettings(
                            url=urljoin("https://justjoin.it/", settings.follow_link),
                            wait_time=1,
                            offer_index=offer_index,
                        ),
                    )

                    # Remember followed links to prevent from scraping duplicates.
                    followed_links.append(follow_link)


@dataclass(frozen=True)
class JustjoinitOfferPageSessionSettings:
    url: str
    wait_time: int
    offer_index: int


class JustjoinitOfferPageSession(Session):
    def page_output(self, response) -> FileOutput:
        timestamp = self.metadata.started_at.strftime(TIMESTAMP_FORMAT)
        partition = YMDPartitioner(after={"ts": timestamp}).get()
        offer_id = self.settings.utl.split("/")[-1]
        filename = Path(f"{self.settings.offer_index:05}-{offer_id}.html")

        return FileOutput(
            content=response.html,
            filename=JUSTJOINIT_HTML_OFFERS_PATH / partition / filename,
        )

    def process(
        self, producer: SeleniumProducer, settings: JustjoinitOfferPageSessionSettings
    ) -> Generator[Output, None, None]:
        response = producer.get(settings.url, wait_time=1)
        yield self.page_output(response)


@task
def main():
    session = JustjoinitSession(
        producer=SeleniumProducer(address=SELENIUM_ADDRESS),
        storer=S3FileStorer(bucket=S3_BUCKET),
        settings=JustjoinitSessionSettings(
            url="https://justjoin.it/all-locations/data",
            init_wait=5,
            scroll_by=100,
            scroll_wait=0.2,
        ),
    )
    session.start()

    session_listing_output_prefix = (
        JUSTJOINIT_HTML_LISTING_PATH / session.storer.partitioner.get_partition()
    )
    session_offers_output_prefix = (
        JUSTJOINIT_HTML_OFFERS_PATH / session.storer.partitioner.get_partition()
    )

    return {
        "listing_prefix": session_listing_output_prefix,
        "offers_prefix": session_offers_output_prefix,
    }


if __name__ == "__main__":
    main()
