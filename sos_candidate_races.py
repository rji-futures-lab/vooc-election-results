from csv import DictReader
from itertools import groupby
import json
import os
from random import randint
from time import sleep

import requests

import s3


SIMULATE_RESULTS = os.getenv('SIMULATE_RESULTS', default=False)


with open('metadata/candidates.csv') as f:
    reader = DictReader(f)
    ALL_CANDIDATES = [c for c in reader if c['name'] not in ['Yes', 'No']]


def get_results(endpoint):
    url = f"https://api.sos.ca.gov/returns/{endpoint}"
    r = requests.get(url)
    r.raise_for_status()

    return r.headers['content-type'], r.content


def get_candidate_id_name_mapping(race_id):
    candidates = [c for c in ALL_CANDIDATES if c['race_id'] == race_id]

    return {
        c['name'].split('/')[0].split()[0]: c['id'] for c in candidates
    }


def format_data(race_id, results):

    mapping = get_candidate_id_name_mapping(race_id)

    formatted = {
        'reporting_time': results['ReportingTime'],
        'candidate_votes': [
            {
                'id': mapping[i['Name'].split()[0]],
                'name': i['Name'], 
                'is_incumbent': i['incumbent'],
                'votes': int(i['Votes'])
            } for i in results['candidates']
        ]
    }

    assert len(formatted['candidate_votes']) == len(mapping)

    return formatted


def main(race_id):
    with open('metadata/sos/candidate-race-endpoints.csv') as f:
        reader = DictReader(f)
        endpoints = [r['endpoint'] for r in reader if r['race_id'] == race_id]

    for endpoint in endpoints:
        content_type, results_json = get_results(endpoint)

        if 'county' in endpoint:
            results = [
                i for i in json.loads(results_json) if 'County' in i['raceTitle']
            ][0]
            results_json = json.dumps(results)

        if SIMULATE_RESULTS:
            results = json.loads(results_json)

            for c in results['candidates']:
                c['Votes'] = str(randint(0, 10000))

            results_json = json.dumps(results)

        results_updated = s3.archive(
            results_json, content_type=content_type, path=f"sos/orig/{endpoint}"
        )

        if results_updated or SIMULATE_RESULTS:
            results = json.loads(results_json)
            formatted_data = format_data(race_id, results)
            formatted_json = json.dumps(formatted_data)
            s3.archive(formatted_json, path=f'sos/formatted/{endpoint}')

        sleep(2)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'race_id', type=str,
    )

    args = parser.parse_args()

    main(args.race_id)
