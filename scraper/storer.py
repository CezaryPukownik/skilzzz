from abc import ABC, abstractmethod
import os
from pathlib import Path
from scraper.logger import logger

from scraper.output import DictOutput, Output, FileOutput
from scraper.partitioner import Partitioner

import boto3

class Storer(ABC):

    @abstractmethod
    def store(self, output: Output):
        ...

    def _on_session_end(self, context):
        ...

    def _on_session_fail(self, context):
        ...

    def _on_output_stored(self, context):
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

    def _on_session_end(self, context):
        self.file_handle.close()

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
    
    def __init__(self, bucket: str, prefix: Path) -> None:
        self.s3 = boto3.client("s3")
        self.bucket = bucket
        self.prefix = prefix
        super().__init__()

    def store(self, output: FileOutput):
        self.s3.put_object(
            Body=str.encode(output.content), 
            Bucket=self.bucket, 
            Key=self.prefix/output.filename
        )

class PartitionedS3FileStorer(Storer):
    
    def __init__(self, bucket: str, prefix: Path, partitioner: Partitioner) -> None:
        self.s3 = boto3.client("s3")
        self.partitioner = partitioner
        self.bucket = bucket
        self.prefix = prefix
        super().__init__()

    def store(self, output: FileOutput):
        partition: Path = self.partitioner.get_partition()
        output_key: Path = self.prefix / partition / output.filename
        output_key: str = str(output_key)
        self.s3.put_object(
            Body=str.encode(output.content), 
            Bucket=self.bucket, 
            Key=output_key
        )
        logger.info(f"Stored FileOutput at s3://{self.bucket}/{output_key}.")

import tempfile
import json
class CompactedPartitionedS3DictStorer(Storer):
    
    def __init__(self, bucket: str, prefix: Path, key: Path, partitioner: Partitioner) -> None:
        self.s3 = boto3.client("s3")
        self.partitioner = partitioner
        self.bucket = bucket
        self.key = key
        self.prefix = prefix
        self.tempfile = tempfile.NamedTemporaryFile()
        super().__init__()

    def store(self, output: DictOutput):
        json_str = json.dumps(output.content, default=str) + "\n"
        self.tempfile.write(str.encode(json_str))
        logger.info(f"Stored DictOutput is temporary file {self.tempfile.name}.")

    def _on_session_end(self, context):
        partition: Path = self.partitioner.get_partition()
        output_key: Path = self.prefix / partition / self.key
        self.s3.upload_file(self.tempfile.name, self.bucket, str(output_key))
        self.tempfile.close()
        logger.info(f"Stored compacted file at s3://{self.bucket}/{output_key}.")
        return super()._on_session_end(context)
        