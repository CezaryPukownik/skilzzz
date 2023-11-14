from abc import ABC, abstractmethod
import os
from pathlib import Path

from scraper.output import Output, FileOutput
from scraper.partitioner import Partitioner

import boto3

class Storer(ABC):

    @abstractmethod
    def store(self, output: Output):
        ...

    
class FileSystemStorer(Storer):

    def __init__(self, path: Path = Path('/')) -> None:
        self.path = path
        super().__init__()

    def store(self, output: FileOutput):
        output_path = self.path / output.filename
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output.content)

class PartialFileSystemStorer(Storer):

    def __init__(self, path: Path) -> None:
        self.path = path
        self.file_handle = open(path, "w")
        super().__init__()

    def store(self, output: Output):
        self.file_handle.write(output.content)


class PartitionedFileSystemStorer(FileSystemStorer):

    def __init__(self, path: Path, partitioner: Partitioner) -> None:
        self.partitioner = partitioner
        super().__init__(path=path)

    def store(self, output: FileOutput):
        partition = self.partitioner.get_partition()
        output_path = self.path / partition / output.filename
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output.content)

class S3FileStorer(Storer):
    
    def __init__(self) -> None:
        self.s3 = boto3.client("s3")
        super().__init__()

    def store(self, output: FileOutput):
        self.s3.upload_file()
