from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Dict


class Partitioner(ABC):
    
    @abstractmethod
    def get_partition(*args, **kwargs) -> Path:
        ...

        
class YMDPartitioner(Partitioner):

    def __init__(
        self, date: Optional[date]=None, before: Dict[str, str]={}, after: Dict[str, str]={}
    ) -> None:

        self.date = date
        self.before = before
        self.after = after

        if not self.date:
            self.date = date.today()
        super().__init__()


    def get(self) -> Path:
        date = self.date
        partition = Path(f"year={date.year}/month={date.month:02d}/day={date.day:02d}/")

        for key, value in self.before.items():
            partition = Path(f"{key}={value}") / partition

        for key, value in self.after.items():
            partition = partition / Path(f"{key}={value}") 

        return partition