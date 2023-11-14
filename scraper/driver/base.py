from abc import ABC, abstractmethod

from scraper.output import Output

class Driver(ABC):

    def _on_session_end(self, context):
        ...

    def _on_output_stored(self, context):
        ...

    def _on_session_fail(self, context):
        ...

    @abstractmethod
    def get(url, *args, **kwargs) -> Output:
        ...
