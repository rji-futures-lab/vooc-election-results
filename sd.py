from itertools import groupby
import json
import os
from random import randint
import xml.etree.ElementTree as et

import requests

from graphics import compile_bar_chart_data, compile_line_chart_data
import s3


SIMULATE_RESULTS = os.getenv('SIMULATE_RESULTS', default=False)


CANDIDATE_ID_MAPPINGS = {
    # Brian Maryott
    "8": "9756",
    # Mike Levin
    "7": "9757",
}


def get_results():
    url = "http://www.livevoterturnout.com/sandiego/liveresults/summary_10.xml"
    r = requests.get(url)
    r.raise_for_status()

    return r.headers['content-type'], r.content


def parse_results(xml):
    root = et.fromstring(xml)

    reporting_time = root.find('./GeneratedDate').text

    xpath = "./Table[RaceID='2']"

    tables = root.findall(xpath)

    results = []

    for table in tables:
        candidate = {c.tag: c.text for c in list(table)}
        if SIMULATE_RESULTS:
            candidate['TotalVotes'] = str(randint(0, 10000))
        results.append(candidate)

    return reporting_time, results


def format_data(race_data, reporting_time):
    return {
        'reporting_time': reporting_time,
        'candidate_votes': [
            {
                'id': CANDIDATE_ID_MAPPINGS[c['ContestantID']],
                'name': c['ContestantName'], 
                # 'is_incumbent': "*" in v['ContestantName'],
                'votes': int(c['TotalVotes'])
            } 
            for c in race_data
        ]
    }


def handle_race(race_data, reporting_time):
    race_json = json.dumps(race_data)
    race_updated = s3.archive(race_json, path=f'sd/parsed/2')

    if race_updated:
        formatted_data = format_data(race_data, reporting_time)
        formatted_json = json.dumps(formatted_data)
        s3.archive(formatted_json, path=f"sd/formatted/2")


def main():
    content_type, results = get_results()

    results_updated = s3.archive(
        results, content_type=content_type, path='sd/orig'
    )

    if results_updated or SIMULATE_RESULTS:
        reporting_time, race_data = parse_results(results)
        handle_race(race_data, reporting_time)


if __name__ == '__main__':
    main()
