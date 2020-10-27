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
    previous_data = s3.read_from(f"bar-graphs/{race_id}/latest.json")

    if previous_data:
        previous_total_ballots = previous_data['total_ballots']
    else:
        previous_total_ballots = 0

    return previous_total_ballots


def get_race_meta_data(race_id):
    with open("races.json") as f:
        race_meta_data = json.loads(f.read())

    return race_meta_data[race_id]


def compile_bar_graph_data(race_id, race_data, reporting_time):

    race_meta_data = get_race_meta_data(race_id)
    candidates_meta_data = race_meta_data['candidates']

    candidates = []

    for c_id, c_data in race_data.items():
        candidate_meta_data = candidates_meta_data[c_id]
        candidate_meta_data["votes"] = int(c_data["TotalVotes"])
        candidate_meta_data["percent"] = c_data["ContestantVotePercent"]
        candidates.append(candidate_meta_data) 

    previous_total_ballots = get_previous_total_ballots(race_id)
    total_ballots = sum([c["votes"] for c in candidates])

    compiled_data = {
        "race_title": race_meta_data["race_title"],
        "reporting_time": reporting_time,
        "total_ballots": total_ballots,
        "ballots_added": total_ballots - previous_total_ballots,
        "candidates": candidates
    }

    return compiled_data


def handle_race(race_id, race_data, reporting_time):
    race_json = json.dumps(race_data)
    race_updated = s3.archive(race_json, path=f'oc/parsed/{race_id}')

    if race_updated:
        bar_graph_data = compile_bar_graph_data(
            race_id, race_data, reporting_time
        )
        bar_graph_data_json = json.dumps(bar_graph_data)
        s3.archive(bar_graph_data_json, path=f"bar-graphs/{race_id}")


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
