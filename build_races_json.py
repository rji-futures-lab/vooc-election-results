from csv import DictReader
from itertools import groupby
import json
import re
from string import capwords

from oc import get_results, parse_results


with open("parties.json") as f:
    PARTIES = json.loads(f.read())


with open("non_party_colors.json") as f:
    NON_PARTY_COLORS = json.loads(f.read())


with open("imgs.csv") as f:
    reader = DictReader(f)

    IMGS = {r['candidate_id']: r['url'] for r in reader}


with open('sos/candidate-race-endpoints.csv') as f:
    reader = DictReader(f)

    sorted_endpoints = sorted([e for e in reader], key=lambda x: x['race_id'])

    SOS_CANDIDATE_RACE_ENDPOINTS = {}

    for r_id, g in groupby(sorted_endpoints, key=lambda x: x['race_id']):
        SOS_CANDIDATE_RACE_ENDPOINTS[r_id] = [e['endpoint'] for e in g]


STATE_PROP_PATTERN = re.compile(r"^Proposition (\d+) - (.+)$")
CITY_MEASURE_PATTERN = re.compile(r"^([A-Z]{1,2})-(.+)$")


def get_color(name, party, sort_order):

    if "MICHAEL TOLAR" in name.upper():
        color = "#62bfff"
    elif name.upper() == "YES" or name.upper() == "NO":
        color = NON_PARTY_COLORS["ballot_measures"][name.lower()]
    elif party:
        color = PARTIES[party]['primary_color']
    else:
        color = NON_PARTY_COLORS["offices"][sort_order]

    return color


def get_img_url(candidate_id):
    try:
        url = IMGS[candidate_id]
    except KeyError:
        url = None

    return url


def format_candidate_name(contestant_name):
    striped = re.sub(r" \(.+\)", "", contestant_name) \
        .lstrip("*") \
        .strip()

    formatted_name = "/".join(
        [capwords(name) for name in striped.split("/")]
    ).rstrip("/")


    if formatted_name.startswith('Linda') and formatted_name.endswith('Sanchez'):
        formatted_name = 'Linda T. Sánchez'
    elif '"' in formatted_name:
        formatted_name = ' "'.join([
            string[0].upper() + string[1:] for string in formatted_name.split(' "')
        ])

    return formatted_name


def format_race_title(race_name):

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
    else:
        formatted_name = race_name
        description = None

    return formatted_name.replace("ORANGE COUNTY", "OC"), description


def get_sos_paths(race_id, race_name):

    try:
        paths = SOS_CANDIDATE_RACE_ENDPOINTS[race_id]
    except KeyError:
        state_prop_match = STATE_PROP_PATTERN.match(race_name)
        if state_prop_match:
            num = state_prop_match.groups()[0]
            paths = [
                f"parsed/ballot-measures/county/orange/{num}"
            ]
        else:
            paths = None

    return paths


def transform(results):
    
    races_by_id = {}

    key_func = lambda x: x['RaceID']
    results.sort(key=key_func)

    for r_id, g in groupby(results, key=key_func):

        contestants = list(g)
        contestants.sort(key=lambda x: x['ContestantID'])
        contestants_by_id = {}

        last_names = [
            format_candidate_name(c['ContestantName']).split()[-1] for c in contestants
        ]
        last_names.sort()

        for c in contestants:
            c_id = c.pop('ContestantID')
            
            candidate_name_orig = c['ContestantName']
            
            party = c['Party']

            candidate_name_formatted = format_candidate_name(candidate_name_orig)

            order_by_last_name = last_names.index(candidate_name_formatted.split()[-1])

            contestants_by_id[c_id] = {
                "name": candidate_name_formatted,
                "party": party,
                "color": get_color(candidate_name_orig, party, order_by_last_name),
                "is_incumbent": "*" in candidate_name_orig,
                "img_url": get_img_url(c_id)
            }

        race_title_orig = contestants[0]['RaceName']
        race_title_formatted, description = format_race_title(race_title_orig)

        races_by_id[r_id] = {
            'race_title': race_title_formatted,
            'candidates': contestants_by_id
        }

        if description:
            races_by_id[r_id]["description"] = description

        sos_paths = get_sos_paths(r_id, race_title_orig)

        if sos_paths:
            races_by_id[r_id]['sos_paths'] = sos_paths

    return races_by_id


def main():
    content_type, results = get_results()
    reporting_time, parsed_results = parse_results(results)
    transformed_results = transform(parsed_results)

    with open('races.json', 'w') as f:
        json.dump(transformed_results, f, indent=4)


if __name__ == '__main__':
    main()
