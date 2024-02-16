from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import Any, Dict

from scraper.producer.html.html import HTMLResponse
from scraper import logger


class Output(ABC):

    def __init__(self, key: str, content: Any):
        self.key = key
        self.content = content
        self.session = None

    @abstractmethod
    def serialize(self):
        ...

    @property
    @abstractmethod
    def format(self):
        """Used to generate file key"""
        ...


class DictOutput(Output):
    format = 'jsonl'

    def __init__(self, key: str, content: Dict[str, Any]):
        super().__init__(key, content)
    
    def serialize(self) -> bytes:
        jsonl_string = json.dumps(self.content, default=str) + "\n"
        return str.encode(jsonl_string)
            

class HTMLOutput(Output):
    format = 'html'

    def __init__(self, key: str, content: HTMLResponse):
        super().__init__(key, content)

    def serialize(self) -> bytes:
        try:
            html_string = self.content.html.prettify()
        except AttributeError as e:
            logger.warning("")
        return str.encode(html_string)