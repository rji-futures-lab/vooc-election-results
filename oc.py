from itertools import groupby
import json
import os
from random import randint
import xml.etree.ElementTree as et

import requests

import s3


SIMULATE_RESULTS = os.getenv('SIMULATE_RESULTS', default=False)


def get_results():
    url = "https://www.livevoterturnout.com/Orange/LiveResults/summary_6.xml"
    r = requests.get(url, verify=False)
    r.raise_for_status()

    return r.headers['content-type'], r.content


def parse_results(xml):
    root = et.fromstring(xml)

    reporting_time = root.find('./GeneratedDate').text

    results = [
        {c.tag: c.text for c in list(table)}
        for table in root.findall('./Table')
    ]

    return reporting_time, results


def group_results(results):
    
    races_by_id = {}

    key_func = lambda x: x['RaceID']
    results.sort(key=key_func)

    for r_id, g in groupby(results, key=key_func):
        
        contestants = list(g)
        contestants.sort(key=lambda x: x['ContestantID'])
        contestants_by_id = {}

        for c in contestants:
            c_id = c.pop('ContestantID')
            if SIMULATE_RESULTS:
                c['TotalVotes'] = str(randint(0, 10000))
            contestants_by_id[c_id] = c
        
        races_by_id[r_id] = contestants_by_id 

    return races_by_id


def format_data(race_data, reporting_time):
    return {
        'reporting_time': reporting_time,
        'candidate_votes': [
            {
                'id': k,
                'name': v['ContestantName'], 
                'is_incumbent': "*" in v['ContestantName'],
                'votes': int(v['TotalVotes'])
            } 
            for k, v in race_data.items()
        ]
    }


def handle_race(race_id, race_data, reporting_time):
    race_json = json.dumps(race_data)
    race_updated = s3.archive(race_json, path=f'oc/parsed/{race_id}')

    if race_updated:
        formatted_data = format_data(race_data, reporting_time)
        formatted_json = json.dumps(formatted_data)
        s3.archive(formatted_json, path=f'oc/formatted/{race_id}')


def main():
    content_type, results = get_results()

    results_updated = s3.archive(
        results, content_type=content_type, path='oc/orig'
    )

    if results_updated or SIMULATE_RESULTS:
        reporting_time, parsed_results = parse_results(results)
        grouped_results = group_results(parsed_results)

        for race_id, race_data in grouped_results.items():
            handle_race(race_id, race_data, reporting_time)


if __name__ == '__main__':
    main()
