from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from threading import Thread
from typing import Generator, Hashable
import uuid
from scraper.logger import logger

from scraper.producer.base import Producer
from scraper.output import Output
from scraper.settings import TIMESTAMP_FORMAT
from scraper.storer import Storer


@dataclass
class SessionSettings:
    ...

@dataclass(frozen=True)
class SessionMetadata:
    session_id: str
    started_at: datetime


class Session(ABC):
    def __init__(self, producer, storer, settings, task_queue=None):
        self.metadata = SessionMetadata(
            session_id=str(uuid.uuid4().hex), started_at=datetime.now()
        )
        self.producer = producer
        self.storer = storer
        self.settings = settings

    def start(self) -> None:
        try:
            with ThreadPoolExecutor(max_workers=8) as executor:
                for signal in self.process(self.producer, self.settings):

                    # Store if session yielded Output
                    if isinstance(signal, str):
                        logger.info(f"Procesing output: {signal}")
                        # self.storer.store(output=signal)
                        # self.storer.on_output_stored()
                        # self.producer.on_output_stored()

                    # Run session, if new session was yielded
                    if isinstance(signal, Session):
                        executor.submit(signal.start)



        except Exception as e:
            self.storer.on_session_fail()
            self.producer.on_session_fail()
            raise e

        finally:
            self.storer.on_session_end()
            self.producer.on_session_end()



    @abstractmethod
    def process(self, producer, settings) -> Generator[Output, None, None]:
        ...
