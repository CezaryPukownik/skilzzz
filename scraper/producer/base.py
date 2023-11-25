from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from scraper.output import Output


class Response(ABC):
    ...

class HTMLResponse(BeautifulSoup):
    def __init__(self, html) -> None:
        super().__init__(html, parser="lxml")

class Producer(ABC):
    def on_session_end(self, context):
        ...

    def on_output_stored(self, context):
        ...

    def on_session_fail(self, context):
        ...

    @abstractmethod
    def get(url, *args, **kwargs) -> Response:
        ...


