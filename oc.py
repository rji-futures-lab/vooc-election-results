from itertools import groupby
import json
import xml.etree.ElementTree as et

import requests

import s3


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
            contestants_by_id[c_id] = c
        
        races_by_id[r_id] = contestants_by_id 

    return races_by_id


def get_previous_total_ballots(race_id):
    previous_data = s3.read_from(f"bar-graphs/{self.race_id}/latest.json")

    try:
        previous_total_ballots = previous_data['totalBallots']
    except IndexError:
        return 0
    except:
        return int(previous_total_ballots)


def compile_bar_graph_data(race_id, race_data, reporting_time):

    previous_total_ballots = get_previous_total_ballots(race_id)

    total_ballots = 0

    candidates = []

    for c_id, c_data in race_data:
        candidates.append()

    compiled_data = {
        "race_title": "",
        "reporting_time": reporting_time,
        "total_ballots": total_ballots,
        "ballots_added": total_ballots - previous_total_ballots,
        "candidates": candidates
    }

    return compiled_data_json


def handle_race(race_id, race_data, reporting_time):
    race_json = json.dumps(race_data)
    race_updated = s3.archive(race_json, path=f'oc/parsed/{race_id}')

    if race_updated:
        bar_graph_data = compile_bar_graph_data(race_id, race_data, reporting_time)
        bar_graph_data_json = json.dumps(compile_bar_graph_data)
        s3.archive(bar_graph_data_json, path=f"bar-graphs/{race_id}/latest.json")


def main():
    content_type, results = get_results()

    results_updated = s3.archive(
        results, content_type=content_type, path='oc/orig'
    )

    if results_updated:
        reporting_time, parsed_results = parse_results(results)
        grouped_results = group_results(parsed_results)

        for race_id, race_data in grouped_results.items():
            handle_race(race_id, race_data, reporting_time)


if __name__ == '__main__':
    main()
