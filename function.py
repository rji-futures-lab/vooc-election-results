import boto3
import os

S3_CLIENT = boto3.client('s3')
PROJECT_NAME = os.getenv('PROJECT_NAME')

def get_cached_results(key):
    params = {
        'Bucket': 'vooc-election-results',
        'Key': key
    }
    response = S3_CLIENT.get_object(**params)
    return response['Body'].read()

def write_to_s3(key, content, content_type):
    params = {
        'Bucket': PROJECT_NAME,
        'ACL': 'public-read',
        'Key': key,
        'Body': content,
        'ContentType': f'{content_type}; charset=UTF-8'
    }
    return S3_CLIENT.put_object(**params)