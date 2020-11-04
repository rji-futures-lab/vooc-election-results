import json
import os

import boto3

import la
import oc
import sd
import sos_ballot_measures
import sos_candidate_races
import graphics


LAMBDA_CLIENT = boto3.client('lambda')


with open("metadata/charts.json") as f:
    CHART_METADATA = json.loads(f.read())


def handle_command(command, args=None):
    payload = {
        'command': command,
    }

    if args:
        payload.update(args)

    return LAMBDA_CLIENT.invoke(
        FunctionName=os.getenv('PROJECT_NAME'),
        InvocationType='Event',
        Payload=json.dumps(payload).encode('utf-8'),
    )


def compile_all_graphics():
    for path in CHART_METADATA:
        handle_command('graphics', args={'path': path})


def route_event(event):
    if event['command'] == 'oc':
        oc.main()
    elif event['command'] == 'la':
        la.main()
    elif event['command'] == 'sd':
        sd.main()
    elif event['command'] == 'sos_ballot_measures':
        sos_ballot_measures.main()
    elif event['command'] == 'sos_candidate_races':
        sos_candidate_races.main()
    elif event['command'] == 'graphics':
        graphics.main(path=event['path'])


def lambda_handler(event, context):
    if 'command' in event:
        route_event(event)
    else:
        main()


def main():
    handle_command('la')
    handle_command('oc')
    handle_command('sd')
    handle_command('sos_ballot_measures')
    handle_command('sos_candidate_races')
    compile_all_graphics()

if __name__ == '__main__':
    main()

