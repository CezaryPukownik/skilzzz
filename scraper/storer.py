from abc import ABC, abstractmethod
import tempfile
import json
import os
from pathlib import Path
from scraper.logger import logger
from urllib.parse import urlparse

from scraper.output import DictOutput, Output, FileOutput
from scraper.partitioner import Partitioner

import boto3


class Storer(ABC):
    @abstractmethod
    def store(self, output: Output):
        ...

    def on_session_end(self, context):
        ...

    def on_session_fail(self, context):
        ...

    def on_output_stored(self, context):
        ...


class LocalFileStorer(Storer):
    def __init__(self, path: Path = Path("/")) -> None:
        self.path = path
        super().__init__()

    def store(self, output: FileOutput):
        output_path = self.path / output.filename
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output.content)


class S3Storer(Storer, ABC):
    def __init__(self, bucket: str, key: str) -> None:
        self.s3 = boto3.client("s3")
        self.bucket = bucket
        self.path = key


class S3FileStorer(S3Storer):

    def store(self, output: FileOutput):
        self.s3.put_object(
            Body=str.encode(output.content),
            Bucket=self.bucket,
            Key=self.key,
        )


class DictOutputSerializer:
    @classmethod
    def as_jsonl(output: DictOutput):
        return json.dumps(output.content, default=str) + "\n"


class LocalDictStorer(Storer):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.file_handle = open(path, "w")
        super().__init__()

    def store(self, output: DictOutput):
        serialized_output = DictOutputSerializer.as_jsonl(output)
        self.file_handle.write(serialized_output)

    def on_session_end(self, context):
        self.file_handle.close()


class S3DictStorer(S3Storer):
    def __init__(self, bucket: str, key: str) -> None:
        super().__init__(bucket=bucket, key=key)
        self.tempfile = tempfile.NamedTemporaryFile()

    def store(self, output: DictOutput):
        serialized_output = DictOutputSerializer.as_jsonl(output)
        self.tempfile.write(str.encode(serialized_output))
        logger.info(f"Stored DictOutput is temporary file {self.tempfile.name}.")

    def on_session_end(self, context):
        self.s3.upload_file(self.tempfile.name, self.bucket, self.key)
        self.tempfile.close()
        logger.info(f"Stored compacted file at s3://{self.bucket}/{self.key}.")
