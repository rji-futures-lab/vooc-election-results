import os

import boto3

import oc
import sd
import sos


LAMBDA_CLIENT = boto3.client('lambda')


def handle_source(source):
    payload = {
        'source': service['name'],
    }

    return LAMBDA_CLIENT.invoke(
        FunctionName=os.getenv('PROJECT_NAME'),
        InvocationType='Event',
        Payload=json.dumps(payload).encode('utf-8'),
    )


def lambda_handler(event, context):
    if 'source' in event:
        if event['source'] == 'oc':
            oc.main()
        elif event['source'] == 'sd':
            sd.main()
        elif event['source'] == 'sos'
            sos.main()
    else:
        handle_source('oc')
        handle_source('sd')
        handle_source('sos')
