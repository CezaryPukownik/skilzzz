from abc import ABC, abstractmethod

from scraper.output import Output

class Driver(ABC):

    @abstractmethod
    def get(url, *args, **kwargs) -> Output:
        ...
