import time
import boto3
import os

sqs = boto3.resource('sqs')

def lambda_handler(event, context):
    print('CONCURRENCY_COUNT_START')
    print("Wait for 10 seconds")
    time.sleep(10)
    queue = sqs.get_queue_by_name(os.environ.get('ORDER_QUEUE_NAME'))
    response = queue.send_message(MessageBody= f'order # {event.get("order_num")}')

    ## Logic Implementation
    print('CONCURRENCY_COUNT_END')

    response = {
        "statusCode": 200,
        "body": "Ok"
    }