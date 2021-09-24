import time

def lambda_handler(event, context):
    print('CONCURRENCY_COUNT_START')
    print("Wait for 10 seconds")
    time.sleep(10)

    ## Logic Implementation
    print('CONCURRENCY_COUNT_END')    
    
    response = {
        "statusCode": 200,
        "body": "Ok"
    }