import json
from rake_nltk import Rake, Metric
from nltk.tokenize import word_tokenize
from thefuzz import fuzz, process
import boto3

if __name__ == '__main__':
    dynamodb_client = boto3.client('dynamodb')
    response = dynamodb_client.list_tables()
    print(response)


