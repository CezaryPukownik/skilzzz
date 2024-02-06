
from typing import Any, List
import requests

from scraper.logger import logger

from scraper.producer.html.html import HTMLProducer, HTMLResponse


class SplashProducer(HTMLProducer):
    def __init__(self, host: str, port: str) -> None:
        self.host = host
        self.port = port
        super().__init__()

    def get(self, url, wait_time:int = 1):
        response = requests.get(f"http://{self.host}:{self.port}/render.html?url={url}&wait={wait_time}")
        return HTMLResponse(response.text)

