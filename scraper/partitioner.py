from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path


class Partitioner(ABC):
    
    @abstractmethod
    def get_partition(*args, **kwargs) -> Path:
        ...

        
class YMDPartitioner(Partitioner):

    def __init__(self, before={}, after={}) -> None:
        self.before = before
        self.after = after
        super().__init__()

    def get_partition(self) -> Path:
        current_date = date.today()
        partition = Path(f"year={current_date.year}/month={current_date.month:02d}/day={current_date.day:02d}/")

        for key, value in self.before.items():
            partition = Path(f"{key}={value}") / partition

        for key, value in self.after.items():
            partition = partition / Path(f"{key}={value}") 

        return partition