import sys
import time
from typing import Any, List

import boto3
from selenium import webdriver

from scraper.logger import logger

from scraper.driver.base import Driver


class S3Driver(Driver):

    def __init__(self, bucket: str) -> None:
        self.s3 = boto3.client("s3")
        self.bucket = bucket
        super().__init__()

    def get(self, key):
        return self.s3.get_object(
            Bucket=self.bucket,
            Key=key
        )['Body'].read()
        
    def list_prefix(self, prefix: str) -> List[str]:
        response = self.s3.list_objects(Bucket=self.bucket, Prefix=prefix)
        return [file['Key'] for file in response['Contents']]