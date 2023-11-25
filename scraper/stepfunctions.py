import json
import os
import boto3
import traceback
      
from scraper.logger import logger
 
def task(func):
    
    def inner(*args, **kwargs):
        if (task_token := os.environ.get('AWS_STEPFUNCTIONS_TASK_TOKEN', None)):
            logger.info("Started task execution within AWS Step Functions.")
            client = boto3.client('stepfunctions')

            try:
                output: dict = func(*args, **kwargs)
                client.send_task_success(
                    taskToken=task_token,
                    output=json.dumps(output, default=str)
                )

            except Exception as e:
                client.send_task_failure(
                    taskToken=task_token,
                    error=str(e)
                    cause=str(traceback.format_exc())
                )
        
        else:
            logger.info("Started task execution locally.")
            return func(*args, **kwargs)

    return inner

                