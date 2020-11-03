import csv
from itertools import groupby
import json
from operator import attrgetter
import re
from string import capwords
import xml.etree.ElementTree as et

from get_races import get_results


with open("metadata/parties.json") as f:
    PARTIES = json.loads(f.read())


with open("metadata/non_party_colors.json") as f:
    NON_PARTY_COLORS = json.loads(f.read())


with open("metadata/imgs.csv") as f:
    reader = csv.DictReader(f)

    IMGS = {r['candidate_id']: r['url'] for r in reader}


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


def get_img_url(contestant_id):
    try:
        url = IMGS[contestant_id]
    except KeyError:
        url = None

    return url


def format_name(contestant_name):
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

    if '-' in formatted_name:
        n = formatted_name.index('-') + 1
        formatted_name = ''.join([
            formatted_name[:n],
            formatted_name[n].upper(),
            formatted_name[n + 1:]
        ])

    if "'" in formatted_name:
        n = formatted_name.index("'") + 1
        formatted_name = ''.join([
            formatted_name[:n],
            formatted_name[n].upper(),
            formatted_name[n + 1:]
        ])

    return formatted_name


def parse_table_element(element):
    
    contestant_id = element.findtext('ContestantID')
    contestant_name = element.findtext('ContestantName')
    formatted_name = format_name(contestant_name)

    return {
        'race_id': element.findtext('RaceID'),
        'id': contestant_id,
        'name': formatted_name,
        'source_name': contestant_name,
        'is_incumbent': "*" in contestant_name,
        'party': element.findtext('Party'),
        'img_url': get_img_url(contestant_id),
    }


def parse_results(xml):
    root = et.fromstring(xml)

    data = [
        parse_table_element(e) for e in root.findall('./Table')
    ]

    data.sort(key=lambda x: x['race_id'])

    out = []

    for r_id, g in groupby(data, key=lambda x: x['race_id']):
        candidates = list(g)
        
        last_names = [c['name'].split()[-1] for c in candidates]
        last_names.sort()

        for candidate in candidates:
            candidate_last_name = candidate['name'].split()[-1]
            order_by_last_name = last_names.index(candidate_last_name)
            candidate['color'] = get_color(
                candidate['source_name'],
                candidate['party'],
                order_by_last_name
            )
            out.append(candidate)

    return out


def main():
    results = get_results()
    parsed_results = parse_results(results)

    with open('metadata/candidates.csv', 'w') as f:
        columns = [
            'race_id',
            'id',
            'name',
            'source_name',
            'is_incumbent',
            'party',
            'img_url',
            'color',
        ]
        writer = csv.DictWriter(f, columns)

        writer.writeheader()

        for row in parsed_results:
            writer.writerow(row)


if __name__ == '__main__':
    main()
