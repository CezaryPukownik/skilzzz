from pathlib import Path
from typing import Any, Dict


class Output:
    def __init__(self, content: Any, metadata: Dict[str, Any] = {}):
        self.content = content
        self.metadata = metadata


class DictOutput(Output):
    def __init__(self, content: Dict[str, Any], metadata: Dict[str, Any] = {}):
        super().__init__(content, metadata)


class FileOutput(Output):
    def __init__(self, content: str, filename: Path, metadata: Dict[str, Any] = {}):
        self.filename = filename
        super().__init__(content, metadata)
