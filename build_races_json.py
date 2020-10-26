from itertools import groupby
import json
import re

from oc import get_results, parse_results


with open("parties.json") as f:
    PARTIES = json.loads(f.read())


with open("non_party_colors.json") as f:
    NON_PARTY_COLORS = json.loads(f.read())


def assign_color(name, party, sort_order):

    if name == "MICHAEL TOLAR":
        color = "#62bfff"
    elif name == "YES" or name == "NO":
        color = NON_PARTY_COLORS["ballot_measures"][name.lower()]
    elif party:
        color = PARTIES[party]['primary_color']
    else:
        color = NON_PARTY_COLORS["offices"][sort_order]

    return color


def format_candidate_name(contestant_name):
    return re.sub(r" \(.+\)", "", contestant_name) \
        .lstrip("*") \
        .strip()


def transform(results):
    
    races_by_id = {}

    key_func = lambda x: x['RaceID']
    results.sort(key=key_func)

    for r_id, g in groupby(results, key=key_func):

        contestants = list(g)
        contestants.sort(key=lambda x: x['ContestantID'])
        contestants_by_id = {}

        race_title_orig = contestants[0]['RaceName']
        race_title_formatted = race_title_orig

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
                "is_incumbent": "*" in candidate_name_orig
            }

        races_by_id[r_id] = {
            'race_title': contestants[0]['RaceName'],
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
