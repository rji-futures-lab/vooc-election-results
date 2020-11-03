from csv import DictReader
from datetime import datetime
from itertools import groupby
import json
import os
from random import randint
from time import sleep

import pytz
import requests

import s3


SIMULATE_RESULTS = os.getenv('SIMULATE_RESULTS', default=False)


ENDPOINTS = [
    "ballot-measures",
    "ballot-measures/county/orange",
]


with open('metadata/candidates.csv') as f:
    reader = DictReader(f)
    ALL_CANDIDATES = [c for c in reader if c['name'] in ['Yes', 'No']]


with open('metadata/races.csv') as f:
    reader = DictReader(f)
    ALL_RACES = [c for c in reader if 'PROPOSITION' in c['title']]


def get_candidate_id_name_mapping(race_id):
    candidates = [c for c in ALL_CANDIDATES if c['race_id'] == race_id]

    return {
        c['name']: c['id'] for c in candidates
    }


def get_prop_race_id(prop_num):
    races = [
        i['id'] for i in ALL_RACES if i['title'] == f"STATE PROPOSITION {prop_num}"
        ]
    assert len(races) == 1
    return races[0]


def get_results(endpoint):
    url = f"https://api.sos.ca.gov/returns/{endpoint}"
    r = requests.get(url)
    r.raise_for_status()

    return r.headers['content-type'], r.content


def format_data(race_id, results, reporting_time):

    mapping = get_candidate_id_name_mapping(race_id)

    rt = reporting_time \
        .replace('a.m.', 'AM') \
        .replace('p.m.', 'PM') 

    dt = datetime.strptime(rt, '%B %d, %Y, %I:%M %p') \
        .astimezone(pytz.timezone('US/Pacific'))

    formatted = {
        'reporting_time': dt.isoformat(),
        'candidate_votes': [
            {
                'id': dt.isoformat(),
                'name': 'No', 
                'votes': int(results['noVotes'])
            },
            {
                'id': mapping['Yes'],
                'name': 'Yes', 
                'votes': int(results['yesVotes'])
            },
        ]
    }

    assert len(formatted['candidate_votes']) == 2
    assert len(mapping) == 2

    return formatted


def handle_ballot_measure(endpoint, reporting_time, results):
    num = results['Number']
    race_id = get_prop_race_id(num)
    formatted_data = format_data(race_id, results, reporting_time)
    formatted_json = json.dumps(formatted_data)
    s3.archive(formatted_json, path=f'sos/formatted/{endpoint}/{num}')


def main():
    for endpoint in ENDPOINTS:
        content_type, results_json = get_results(endpoint)

        if SIMULATE_RESULTS:
            results = json.loads(results_json)

            for bm in results['ballot-measures']:
                bm['yesVotes'] = str(randint(0, 10000))
                bm['noVotes'] = str(randint(0, 10000))

            results_json = json.dumps(results)

        results_updated = s3.archive(
            results_json, content_type=content_type, path=f"sos/orig/{endpoint}"
        )

        if results_updated or SIMULATE_RESULTS:
            results = json.loads(results_json)
            reporting_time = results['ReportingTime']
            for i in results['ballot-measures']:
                handle_ballot_measure(endpoint, reporting_time, i)

        sleep(2)

if __name__ == '__main__':
    main()
