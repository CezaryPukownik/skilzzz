from abc import ABC, abstractmethod
from pathlib import Path
import tempfile
from typing import Literal

import boto3


from scraper.logger import logger
from scraper.settings import S3_BUCKET

# IDEA: Make this context manager compatible?
class Storage(ABC):
    """Responsible for handling I/O with storage type"""
    def __init__(self) -> None:
        self.opened = {}

    @abstractmethod
    def open(self, file):
        logger.info(f"Opened file {file} using {self.__class__.__name__} storage.")
        ...
    
    @abstractmethod
    def load(self, file: Path):
        logger.info(f"Loaded file {file} using {self.__class__.__name__} storage.")
        ...

    @abstractmethod
    def write(self, file: Path, content: bytes):
        logger.info(f"Written file {file} using {self.__class__.__name__} storage.")
        ...

    @abstractmethod
    def close(self, file: Path):
        logger.info(f"Closed file {file} using {self.__class__.__name__} storage.")
        ...


class FileSystemStorage(Storage):

    def open(self, file: Path):
        file.parent.mkdir(parents=True, exist_ok=True)
        self.opened[file] = open(file, 'wb')
        super().open(file)

        
    def load(self, file: Path):
        with open(file, "r") as f:
            content =  f.read()
        super().load(file)
        return content

    def write(self, file: Path, content: bytes):
        self.opened[file].write(content)
        super().write(file, content)

    def close(self, file: Path):
        self.opened[file].close()
        del self.opened[file]
        super().close(file)


class S3Storage(Storage):
    def __init__(self, bucket) -> None:
        self.s3 = boto3.client("s3")
        self.bucket = bucket
        super().__init__()
        
    def open(self, file: Path):
        self.opened[file] = tempfile.NamedTemporaryFile()
        super().open(file)

    def load(self, file: Path):
        s3_object = self.s3.get_object(Bucket=self.bucket, Key=file)
        content = s3_object["Body"].read().decode('utf-8')
        super().load(file)
        return content

    def write(self, file: Path, content: bytes):
        self.opened[file].write(content)
        super().write(file, content)

    def close(self, file: Path):
        self.s3.upload_file(self.opened[file].name, self.bucket, file)
        self.opened[file].close()
        del self.opened[file]
        super().close(file)

def create_storage(type: Literal['fs', 's3']):
    if type=="fs":
        return FileSystemStorage()

    elif type=="s3":
        return S3Storage(bucket=S3_BUCKET)
        
