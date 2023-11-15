import boto3

def send_success(task_token: str, output: str):
    client = boto3.client('stepfunctions')
    client.send_task_success(
        taskToken=task_token,
        output=output
    )