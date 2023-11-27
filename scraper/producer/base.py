from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from scraper.output import Output


class Response(ABC):
    ...

class HTMLResponse(BeautifulSoup):
    def __init__(self, html) -> None:
        super().__init__(html, "lxml")

class Producer(ABC):
    def on_session_end(self):
        ...

    def on_output_stored(self):
        ...

    def on_session_fail(self):
        ...

    @abstractmethod
    def get(url, *args, **kwargs) -> Response:
        ...


