from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

@dataclass
class Output:
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DictOutput:
    content: dict
    metadata: dict = field(default_factory=dict)

@dataclass
class FileOutput:
    content: Any
    filename: Path
    metadata: Dict[str, Any] = field(default_factory=dict)
