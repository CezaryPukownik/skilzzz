from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from scraper.settings import TIMESTAMP_FORMAT

class Partitioner(ABC):
    
    @abstractmethod
    def get(*args, **kwargs) -> Path:
        ...

        
class YMDTSPartitioner(Partitioner):

    def __init__(self, dt: Optional[datetime]=None) -> None:
        self.dt = dt
        if not self.dt:
            self.dt = datetime.now()


    def get(self) -> Path:
        timestamp = self.dt.strftime(TIMESTAMP_FORMAT)
        partition = Path(
            f"year={self.dt.year}/month={self.dt.month:02d}/day={self.dt.day:02d}/ts={timestamp}"
        )

        return partition
    
