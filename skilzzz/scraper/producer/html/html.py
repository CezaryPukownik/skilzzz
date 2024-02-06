from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from scraper.producer.base import Producer, Response

class HTMLResponse(BeautifulSoup, Response):
    def __init__(self, html) -> None:
        super().__init__(html, "lxml")

class HTMLProducer(Producer, ABC):
    
    @abstractmethod
    def get(self, url:str, wait_time: int) -> HTMLResponse:
        ...
