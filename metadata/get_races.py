from csv import DictWriter
from itertools import groupby
import os
import re
from string import capwords
import xml.etree.ElementTree as et

import requests


STATE_PROP_PATTERN = re.compile(r"^Proposition (\d+) - (.+)$")
CITY_MEASURE_PATTERN = re.compile(r"^([A-Z]{1,2})-(.+)$")


def get_results(use_cache=True):
    url = "https://www.livevoterturnout.com/Orange/LiveResults/summary_6.xml"
    cache_path = 'metadata/.cache'
    file_path = f"{cache_path}/{url.split('/')[-1]}"
    if os.path.exists(file_path) and use_cache:
        with open(file_path) as f:
            results = f.read()
    else:
        r = requests.get(url, verify=False)
        r.raise_for_status()
        results = r.content

        with open(file_path, 'wb') as f:
            f.write(results)

    return results


def parse_data(xml):
    root = et.fromstring(xml)

    data = set(
        (e.find('RaceID').text, e.find('RaceName').text) 
        for e in root.findall('./Table')
    )

    assert len(data) == 181
    
    return sorted(list(data), key=lambda x: x[0])


def has_line_chart(race_id):
    return race_id in [
        1120, 1130, 1140, 1170, 1180, 1200, 1240,
        1320, 1340, 4001
    ]


def format_data(race_id, race_name):

    state_prop_match = STATE_PROP_PATTERN.match(race_name)
    city_measure_match = CITY_MEASURE_PATTERN.match(race_name)

    if state_prop_match:
        num, title = state_prop_match.groups()
        formatted_name = f"STATE PROPOSITION {num}"
        description = capwords(title)
    elif city_measure_match:
        identifier, desc = city_measure_match.groups()
        formatted_name = f"City Ballot Measure {identifier}"
        description = desc
    elif "Governing Board Member" in race_name:
        if "Governing Board Member," in race_name:
            formatted_name = race_name \
                .replace("Governing Board Member,", "—") \
                .strip()
        else:
            formatted_name = race_name \
                .replace("Governing Board Member", "") \
                .strip()
        description = "Governing Board Member"

    else:
        formatted_name = race_name
        description = None

    formatted_name = formatted_name \
        .replace("Orange County", "OC") \
        .replace("ORANGE COUNTY", "OC")

    return {
        'id': race_id,
        'title': formatted_name,
        'source_title': race_name,
        'description': description,
        'has_bar_chart': True,
        'has_line_chart': has_line_chart(race_id),
    }


def main():
    results = get_results()

    with open('metadata/races.csv', 'w') as f:
        columns = [
            'id', 'title', 'source_title', 'description',
            'has_bar_chart', 'has_line_chart'
            ]
        writer = DictWriter(f, columns)

        writer.writeheader()

        for race_id, race_name in parse_data(results):
            row = format_data(race_id, race_name)
            writer.writerow(row)


if __name__ == '__main__':
    main()
