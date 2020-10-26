from csv import DictReader
from itertools import groupby
import json
import re

from oc import get_results, parse_results


with open("parties.json") as f:
    PARTIES = json.loads(f.read())


with open("non_party_colors.json") as f:
    NON_PARTY_COLORS = json.loads(f.read())


with open("imgs.csv") as f:
    reader = DictReader(f)

    IMGS = {r['candidate_id']: r['url'] for r in reader}


STATE_PROP_PATTERN = re.compile(r"^Proposition (\d+) - (.+)$")
CITY_MEASURE_PATTERN = re.compile(r"^([A-Z]{1,2})-.+$")


def assign_color(name, party, sort_order):

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


def to_title_case(string):
    return " ".join(
        [word[0].upper() + word[1:].lower() for word in string.split()]
    )


def format_candidate_name(contestant_name):
    striped = re.sub(r" \(.+\)", "", contestant_name) \
        .lstrip("*") \
        .strip()

    formatted_name = ""

    for name in striped.split('/'):
        title_case = to_title_case(name)
        formatted_name += title_case
        formatted_name += "/"

    return formatted_name.rstrip("/")


def format_race_title(race_name):

    state_prop_match = STATE_PROP_PATTERN.match(race_name)
    city_measure_match = CITY_MEASURE_PATTERN.match(race_name)

    if state_prop_match:
        num, title = state_prop_match.groups()
        formatted_name = f"STATE PROPOSITION {num} - {to_title_case(title)}"
    elif city_measure_match:
        identifier = city_measure_match.groups()[0]
        formatted_name = f"City Ballot Measure {identifier}"
    else:
        formatted_name = race_name

    return formatted_name.replace("ORANGE COUNTY", "OC")


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
                "color": assign_color(candidate_name_orig, party, order_by_last_name),
                "is_incumbent": "*" in candidate_name_orig,
                "img_url": get_img_url(c_id)
            }

        race_title_orig = contestants[0]['RaceName']
        race_title_formatted = format_race_title(race_title_orig)

        races_by_id[r_id] = {
            'race_title': race_title_formatted,
            'candidates': contestants_by_id
        }

    return races_by_id


def main():
    content_type, results = get_results()
    reporting_time, parsed_results = parse_results(results)
    transformed_results = transform(parsed_results)

    with open('races.json', 'w') as f:
        json.dump(transformed_results, f, indent=4)


if __name__ == '__main__':
    main()
