from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal
from scraper.partitioner import YMDTSPartitioner

from scraper.output import Output 
from scraper.storage import Storage, create_storage


class Storer(ABC):
    """Responsible for implementing strategies of storing output"""
    def __init__(self, storage: Literal['fs', 's3']):
        self.storage: Storage = create_storage(storage)

    @abstractmethod
    def store(self, output: Output) -> Path:
        ...

    def on_session_end(self):
        ...

    def on_session_fail(self):
        ...

    def on_output_stored(self):
        ...

    def get_path(self, output: Output) -> Path:
        # This has nothing to do with storer anymore. This should be a output thing.
        partition = YMDTSPartitioner(dt=output.session.metadata.session_dt).get()
        session_root = Path(f"sources/{output.session.name}/{output.session.collection}/{output.format}")
        return session_root / partition / output.key

class OverwriteStorer(Storer):
    """This storer will it create or overwrite file with given key."""

    def store(self, output: Output):
        content = output.serialize()
        output_path = self.get_path(output)
        
        self.storage.open(output_path)
        self.storage.write(output_path, content)
        self.storage.close(output_path)

        return str(output_path)


class AppendStorer(Storer):
    """This storer will append serialized output to asset with same key."""

    def store(self, output: Output):
        content = output.serialize()
        output_path = self.get_path(output)

        if not output_path in self.storage.opened:
            self.storage.open(output_path)

        self.storage.write(output_path, content)
        return str(output_path)

    def on_session_end(self):
        for opened in self.storage.opened:
            self.storage.close(opened)


# Idea for new kind of storer. Batch storer. 
# Store n items in memory and write to a file in
# batches instead of every file every time. 

