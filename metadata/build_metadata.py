from distutils.util import strtobool
import csv
from itertools import groupby
import json


with open('metadata/sources.csv') as f:
    
    reader = csv.DictReader(f)

    SOURCES = [r for r in reader]


def get_races():
    with open('metadata/races.csv') as f:
        reader = csv.DictReader(f)

        races = [r for r in reader]

    races.sort(key=lambda x: x['id'])

    return races


def get_candidates_by_race_id():
    with open('metadata/candidates.csv') as f:
        reader = csv.DictReader(f)

        sources = [r for r in reader]

    sources.sort(key=lambda x: x['race_id'])

    by_race_id = {}

    for r, g in groupby(sources, key=lambda x: x['race_id']):
        candidates = [
        {
            'id': c['id'],
            'name': c['name'],
            'is_incumbent': bool(strtobool(c['is_incumbent'])),
            'party': c['party'],
            'color': c['color'],
            'img_url': c['img_url'],
        }
        for c in list(g)]

        by_race_id[r] = candidates

    return by_race_id


def get_sources_by_chart_path():
    with open('metadata/charts_sources.csv') as f:
        reader = csv.DictReader(f)

        candidates = [r for r in reader]

    candidates.sort(key=lambda x: x['chart_data_path'])

    by_chart_path = {}

    for r, g in groupby(candidates, key=lambda x: x['chart_data_path']):
        by_chart_path[r] = [i['parsed_data_path'] for i in list(g)]

    return by_chart_path


def get_charts(race):

    chart_data = {
        "race_id": race['id'],
        "title": race['title'],
        "description": race['description'],
        "candidates": race['candidates']
    }
    
    has_statewide_chart = (
        "PRESIDENT" in chart_data['title'].upper() or 
        "PROPOSITION" in chart_data['title'].upper()
    )

    if has_statewide_chart:
        statewide_chart = chart_data.copy()
        statewide_chart['title'] = f"{chart_data['title']} — Statewide Results"
        oc_chart = chart_data.copy()
        oc_chart['title'] = f"{chart_data['title']} — OC Results"

        charts = {
            f"bar-charts/{race['id']}": oc_chart,
            f"line-charts/{race['id']}": oc_chart,
            f"bar-charts/{race['id']}/statewide": statewide_chart,
            f"line-charts/{race['id']}/statewide": statewide_chart,
        }
    else:
        charts = {
            f"bar-charts/{race['id']}": chart_data,
            f"line-charts/{race['id']}": chart_data,
        }

    return charts


def get_source_label(sources):

    source_labels = []

    for source in sources:
        source_id = source.split('/')[0]

        if source_id == 'bar-charts':
            pass
        else:
            source_lookup = [s['name'] for s in SOURCES if s['id'] == source_id]
            assert len(source_lookup) == 1
            source_labels.append(source_lookup[0])

    source_label = ", " \
        .join(source_labels) \
        .strip(',') \
        .strip() \
        .replace('Registrar of Voters,', 'and', 1)

    return source_label


def main():

    charts_meta_data = {}

    candidates_by_race_id = get_candidates_by_race_id()
    sources_by_chart_path = get_sources_by_chart_path()

    for race in get_races():
        race['candidates'] = candidates_by_race_id[race['id']]
        race_charts = get_charts(race)

        for k, v in race_charts.items():
            chart = v.copy()
            sources = sources_by_chart_path[k]
            chart['sources'] = sources
            chart['source_label'] = get_source_label(sources)
            
            charts_meta_data[k] = chart

    with open('metadata/charts.json', 'w') as f:
        as_json = json.dump(charts_meta_data, f, indent=4)


if __name__ == '__main__':
    main()
