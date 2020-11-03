from datetime import datetime
from itertools import groupby
import json
import os
from random import randint
import xml.etree.ElementTree as et

import pytz
import requests

import s3


SIMULATE_RESULTS = os.getenv('SIMULATE_RESULTS', default=False)


CONTESTS = {
    # UNITED STATES REPRESENTATIVE 38th District
    'cc7463': {
        'race_id': '1120',
        'candidate_id_mappings': {
            # Linda T. Sánchez
            '18100': "9744",
            # Michael Tolar
            '18101': "9745",
        }
    },
    # UNITED STATES REPRESENTATIVE 39th District
    'cc7464': {
        'race_id': '1130',
        'candidate_id_mappings': {
            # Young Kim
            '18090': "9746",
            # Gil Cisneros
            '18089': "9747",
        }
    },
    # UNITED STATES REPRESENTATIVE 47th District
    'cc7468': {
        'race_id': '1160',
        'candidate_id_mappings': {
            # Alan Lowenthal
            '18097' : "9752",
            # John Briscoe
            '18098': "9753",
        }
    },
    # STATE SENATOR 29th District
    'cc7424': {
        'race_id': '1200',
        'candidate_id_mappings': {
            # Josh Newman
            '18019': "9758",
            # Ling Ling Chang
            '18018': "9759",
        }
    },
    # MEMBER OF THE STATE ASSEMBLY 55th District
    'cc7442': {
        'race_id': '1300',
        'candidate_id_mappings': {
            # Phillip Chen
            '18048': "9762",
            # Andrew E. Rodriguez
            '18047': "9763",
        }
    },
}


def get_results():
    url = "https://rrcc.co.la.ca.us/results/results-06037-2020-11-03.xml"
    r = requests.get(url)
    r.raise_for_status()

    return r.headers['content-type'], r.content


def parse_contests(xml):
    root = et.fromstring(xml)

    reporting_time = root.findtext('GeneratedDate')

    data = {}

    for la_contest_id, contest in CONTESTS.items():
        contest_xpath = f".//Contest[@objectId='{la_contest_id}']"
        contest_element = root.find(contest_xpath)

        candidate = {}
        
        for la_cand_id, oc_cand_id in contest['candidate_id_mappings'].items():
            name_xpath = f".//Person[@objectId='per{la_cand_id}']/FullName/Text"
            votes_xpath = f"BallotSelection[@objectId='cs{la_cand_id}']//VoteCounts[Type='total']/Count"
            candidate[oc_cand_id] = {
                'name': root.findtext(name_xpath),
                'votes': contest_element.findtext(votes_xpath),
            }

            if SIMULATE_RESULTS:
                candidate[oc_cand_id]['votes'] = str(randint(0, 10000))
        
        oc_race_id = contest['race_id']
        data[la_contest_id] = candidate

    return reporting_time, data


def format_data(race_data, reporting_time):

    dt = datetime.fromisoformat(reporting_time) \
        .astimezone(pytz.timezone('US/Pacific'))

    return {
        'reporting_time': dt.isoformat(),
        'candidate_votes': [
            {
                'id': k,
                'name': v['name'], 
                # 'is_incumbent': "*" in v['ContestantName'],
                'votes': int(v['votes']),
            } 
            for k, v in race_data.items()
        ]
    }


def handle_race(race_id, race_data, reporting_time):
    race_json = json.dumps(race_data)
    race_updated = s3.archive(race_json, path=f'la/parsed/{race_id}')

    if race_updated:
        formatted_data = format_data(race_data, reporting_time)
        formatted_json = json.dumps(formatted_data)
        s3.archive(formatted_json, path=f'la/formatted/{race_id}')


def main():
    content_type, results = get_results()

    results_updated = s3.archive(
        results, content_type=content_type, path='la/orig'
    )

    if results_updated or SIMULATE_RESULTS:
        reporting_time, contests = parse_contests(results)
        
        for c_id, c_data in contests.items():
            handle_race(c_id, c_data, reporting_time)


if __name__ == '__main__':
    main()
