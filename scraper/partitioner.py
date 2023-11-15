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
        self, base_date: Optional[date]=None, before: Dict[str, str]={}, after: Dict[str, str]={}
    ) -> None:

        self.base_date = base_date
        self.before = before
        self.after = after

        if not self.base_date:
            self.base_date = date.today()
        super().__init__()


    def get_partition(self) -> Path:
        base_date = self.base_date
        partition = Path(f"year={base_date.year}/month={base_date.month:02d}/day={base_date.day:02d}/")

        for key, value in self.before.items():
            partition = Path(f"{key}={value}") / partition

        for key, value in self.after.items():
            partition = partition / Path(f"{key}={value}") 

        return partition