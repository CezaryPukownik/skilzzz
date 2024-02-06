from abc import ABC, abstractmethod
from bs4 import BeautifulSoup


class Response(ABC):
    ...



class Producer(ABC):
    def on_session_end(self):
        """This method is called by session when session ends"""
        ...

    def on_output_stored(self):
        """This method is called by session when output was stored"""
        ...

    def on_session_fail(self):
        """This method is called by session when session logic raises and error"""
        ...

    @abstractmethod
    def get(*args, **kwargs) -> Response:
        ...


