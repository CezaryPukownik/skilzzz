import json
import click

from dataclasses import dataclass
from datetime import datetime
from typing import Generator, List
from scraper.producer.storage import StorageProducer
from scraper.output import Output, DictOutput
from scraper.session import Session, SessionMetadata
from scraper.settings import TIMESTAMP_FORMAT
from scraper.stepfunctions import stepfunctions_callback_handler
from scraper.storer import AppendStorer
from scraper.logger import logger
from scraper.parsers.exceptions import InvalidHTMLDocument
from scraper.parsers.justjoinit import parsers

from bs4 import BeautifulSoup
import re

import traceback



class JustjoinitStorer(AppendStorer):
    """
    In this case we dont want to close file after ending session
    because item will be yielded by child session. Files will be 
    manually closed by main session.
    """
    def on_session_end(self):
        pass


@dataclass(frozen=True)
class JustjoinitOffersFanoutSettings:
    pattern: str

@dataclass(frozen=True)
class JustjoinitOfferParserSettings:
    file: str

class JustjoinitOffersFanout(Session):
    """
    CAUTION: Always run at minimum whole session run! 
    Running single html will most likely result in missing data.
    """

    def process(self) -> Generator[Output, None, None]:
        files = self.producer.glob(pattern=self.settings.pattern)
        for file in files:
            logger.info(f"Created parsing session for file {file}")
            yield JustjoinintOfferParser(
                name=self.name,
                collection=self.collection,
                producer=self.producer,
                storer=self.storer,
                settings=JustjoinitOfferParserSettings(
                    file=file
                )
            )
        else:
            logger.info(f"No files is given pattern {self.settings.pattern}")

    def after_process(self):
        # Mannualy closed all opened files after.
        opened = [file for file, _ in self.storer.storage.opened.items()]
        for file in opened:
            self.storer.storage.close(file)

class JustjoinintOfferParser(Session):
                
    def process(self) -> Generator[Output, None, None]:
        try:
            # Getting ts from files session.
            if not (match := re.findall("ts=([0-9]{14})/([0-9]{5})-(.*).html", self.settings.file)):
                raise ValueError("Cannot parse ts from filepath corrently")

            # Act as continuation of file processing session
            session_ts, offer_index, offer_id = match[0]
            session_dt = datetime.strptime(session_ts, TIMESTAMP_FORMAT)
            self.metadata = SessionMetadata(
                session_dt = session_dt,
                session_ts = session_ts
            ) 
            
            # Load html from filesystem
            file_content = self.producer.get(self.settings.file)
            logger.info(f"Loaded {self.settings.file} from {self.producer.__class__.__name__}")

            soup = BeautifulSoup(file_content, "lxml")

            parser_func = parsers['v1']
            
            parsed_offer = parser_func(soup)
            yield DictOutput(
                key=f"justjoinit-offers-{session_ts}.jsonl",
                content={
                    "listed_at": session_ts, 
                    "offer_index": offer_index,
                    "offer_id": offer_id,
                    **parsed_offer
                }
            )
        except InvalidHTMLDocument as e:
            logger.error(f"Cannot parse file {self.settings.file} due to recognized invalid html. {e}")
        except Exception as e:
            traceback_str = "".join(traceback.format_tb(e.__traceback__))
            logger.critical(f"Cannot parse file {self.settings.file}. Unhandled exception:\n{e}\n{traceback_str}")
                    
        
@click.command()
@click.option("--pattern")
@click.option("--read", default='fs')
@click.option("--write", default='fs')
@stepfunctions_callback_handler
def main(pattern, read, write):
    assets = JustjoinitOffersFanout(
        name="justjoinit",
        collection="offers",
        producer=StorageProducer(storage=read),
        storer=JustjoinitStorer(storage=write),
        settings=JustjoinitOffersFanoutSettings(
            pattern=pattern
        )
    ).start()

    logger.info("Session output:\n" + json.dumps(assets, indent=4))
    return assets

if __name__=="__main__":
    main()