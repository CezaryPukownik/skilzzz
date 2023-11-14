from abc import ABC, abstractmethod
from typing import Generator, Hashable

from scraper.driver.chrome_selenium_remote import ChromeSeleniumRemoteDriver
from scraper.driver.base import Driver
from scraper.output import Output
from scraper.storer import Storer, PartitionedFileSystemStorer
from scraper.partitioner import YMDPartitioner

class Session(ABC):

    def __init__(self, driver: Driver, storer: Storer):
        self.driver = driver
        self.storer = storer

    def start(self, context: Hashable) -> None:
        try:
            for output in self.generate_outputs(driver=self.driver, context=context):
                self.storer.store(output=output)

                self.storer._on_output_stored(context)
                self.driver._on_output_stored(context)

        except Exception as e:
            self.storer._on_session_fail(context)
            self.driver._on_session_fail(context)
            raise e
            
        finally:
            self.storer._on_session_end(context)
            self.driver._on_session_end(context)



    @abstractmethod
    def generate_outputs(self, driver, context) -> Generator[Output, None, None]:
        ...

       