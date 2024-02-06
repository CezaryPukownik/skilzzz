from abc import ABC, abstractmethod
import fnmatch
import glob
import os
import re
from typing import List, Literal

from scraper.producer.base import Producer
from scraper.settings import S3_BUCKET
from scraper.storage import S3Storage
from scraper.storage import FileSystemStorage

class BaseStorageProducer(Producer, ABC):
    
    @abstractmethod
    def get(self, file) -> str:
        ...

    @abstractmethod
    def glob(self, pattern) -> List[str]:
        ...
    

class S3Producer(BaseStorageProducer, S3Storage):

    def get(self, file):
        return self.load(file=file)

    def glob(self, pattern):
        """Return a list of file paths in an S3 bucket that match the glob_pattern."""
        paginator = self.s3.get_paginator('list_objects_v2')

        # Extract the initial prefix from the glob pattern for efficient filtering
        # by S3 (reduces the amount of data transferred).
        prefix = pattern.split('*')[0][:-1]

        all_filepaths = []
        filtered_filepaths = []

        # Pagination is used for large buckets that can't be listed in a single API call
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            # Checking if 'Contents' exists to avoid cases where the prefix has no matches
            if 'Contents' in page:
                for obj in page['Contents']:
                    all_filepaths.append(obj['Key'])

        # Use fnmatch to filter the filepaths according to the glob_pattern
        for filepath in all_filepaths:
            if fnmatch.fnmatch(filepath, pattern):
                filtered_filepaths.append(filepath)

        return filtered_filepaths

class FileSystemProducer(BaseStorageProducer, FileSystemStorage):
    def get(self, key):
        return self.load(file=key)

    def glob(self, pattern: str) -> List[str]:
        return glob.glob(pattern)

class StorageProducer(BaseStorageProducer):
    def __init__(self, storage: Literal['fs', 's3']) -> None:
        if storage == "fs":
            self.storage = FileSystemProducer()
        elif storage == "s3":
            self.storage = S3Producer(bucket=S3_BUCKET)
        else:
            raise ValueError(f"Unsupported storeage type {storage}.")

    def get(self, file) -> str:
        return self.storage.get(file)

    def glob(self, pattern) -> str:
        return self.storage.glob(pattern)