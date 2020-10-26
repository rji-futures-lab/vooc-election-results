from datetime import datetime
import os

import boto3


S3_CLIENT = boto3.client('s3')
PROJECT_NAME = os.getenv('PROJECT_NAME')


def read_from(key):
    params = {
        'Bucket': PROJECT_NAME,
        'Key': key
    }
    try:
        response = S3_CLIENT.get_object(**params)
    except S3_CLIENT.exceptions.NoSuchKey:
        return None
    else:
        return response['Body'].read()


def write_to(key, content, content_type):
    params = {
        'Bucket': PROJECT_NAME,
        'ACL': 'public-read',
        'Key': key,
        'Body': content,
        'ContentType': content_type
    }
    return S3_CLIENT.put_object(**params)


def archive(content, content_type="application/json", path=''):
    ext = content_type.split(";")[0].split("/")[-1]
    latest_key = f"{path}/latest.{ext}"

    previous_content = read_from(latest_key)

    has_diffs = content != previous_content

    if has_diffs:
        recorded_at_key = f"{path}/{datetime.now()}.{ext}"
        write_to(latest_key, content, content_type)
        write_to(recorded_at_key, content, content_type)

    return has_diffs
