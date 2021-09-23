import boto3

def handler(event, context):
    for record in event['Records']:
        print("test")
        payload = record["body"]
        print(str(payload))


