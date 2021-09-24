import json
from transformers import pipeline
import time

def get_nlp_model():
    print("-----------Downloading NLP model ------------------")
    time.sleep(100)
    return pipeline("sentiment-analysis")
    
nlp = get_nlp_model()

def handler(event, context):
    time.sleep(10)
    print(event)
    nlp_response =  nlp(event['text'])[0]
    print(nlp_response)
        
    response = {
        "statusCode": 200,
        "body": nlp_response
    }
    return response
    

