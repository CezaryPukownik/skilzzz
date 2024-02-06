
import time
import requests

from scraper.producer.html.html import HTMLProducer, HTMLResponse

class RESTProducer(HTMLProducer):
    def __init__(self) -> None:
        super().__init__()

    def get(self, url, wait_time: int = None) -> HTMLResponse:
        if wait_time:
            time.sleep(wait_time)
        response = requests.get(url)
        return HTMLResponse(response.text)