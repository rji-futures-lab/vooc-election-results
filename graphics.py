from itertools import groupby
import json

import s3


with open("metadata/charts.json") as f:
    CHART_METADATA = json.loads(f.read())


def get_previous_total_ballots(path):
    previous_data = s3.read_from(f"{path}/latest.json")

    if previous_data:
        as_dict = json.loads(previous_data)
        previous_total_ballots = as_dict['total_ballots']
    else:
        previous_total_ballots = 0

    return previous_total_ballots


def get_candidate_race_source_data(path):
    source_data = s3.read_from(f"{path}/latest.json")

    if source_data:
        as_dict = json.loads(source_data)
    else:
        data = None

    return data


def get_source_data(path):
    source_data = s3.read_from(f"{path}/latest.json")
    as_dict = json.loads(source_data)

    return as_dict


def compile_bar_chart_data(path):

    meta_data = CHART_METADATA[path].copy()
    sources = meta_data['sources']
    source_data = [get_source_data(path) for path in sources]

    reporting_times = sorted([i['reporting_time'] for i in source_data], reverse=True)
    
    candidate_votes = []
    for i in source_data:
        for j in i['candidate_votes']:
            candidate_votes.append(j)

    previous_total_ballots = get_previous_total_ballots(path)
    total_ballots = sum([c["votes"] for c in candidate_votes])

    candidate_votes.sort(key=lambda x: x['id'])

    candidate_image_count = 0
    candidates = []

    for c_id, g in groupby(candidate_votes, key=lambda x: x['id']):
        candidate_lookup = [c for c in meta_data['candidates'] if c['id'] == c_id]
    
        assert len(candidate_lookup) == 1

        candidate = candidate_lookup[0]
        
        candidate_votes_total = sum([i["votes"] for i in g])
        candidate_pct = round((candidate_votes_total / total_ballots) * 100, 2)
        
        candidate['votes'] = candidate_votes_total
        candidate["percent"] = candidate_pct
        candidate["is_incumbent"] = candidate['is_incumbent']

        if candidate['img_url']:
            candidate_image_count += 1

        candidates.append(candidate)

    chart_data = {
        "race_title": meta_data['title'],
        "reporting_time": reporting_times[0],
        "total_ballots": total_ballots,
        "ballots_added": total_ballots - previous_total_ballots,
        "source": meta_data['source_label'],
        "use_candidate_images": candidate_image_count == len(candidates),
        "candidates": candidates,
    }

    if len(meta_data['description']) > 0:
        chart_data['description'] = meta_data['description']

    return chart_data


def compile_line_chart_data(path):
    
    previous_data = s3.read_from(f"{path}/latest.json")
    meta_data = CHART_METADATA[path]

    assert len(meta_data['sources']) == 1
    source_data_path = meta_data['sources'][0]

    if previous_data:
        chart_data = json.loads(previous_data)
    else:
        chart_data = {
            "race_title": meta_data["title"],
            "latest_reporting_time": "",
            "latest_total_ballots": 0,
            "source": CHART_METADATA[source_data_path]['source_label'],
            "latest_ballots_added": 0,
            "updates": {
                "race_wide": [],
                "per_candidate": []
            }
        }

    if len(meta_data['description']) > 0:
        chart_data['description'] = meta_data['description']

    source_data = json.loads(s3.read_from(f"{source_data_path}/latest.json"))

    chart_data["latest_reporting_time"] = source_data["reporting_time"]
    chart_data["latest_total_ballots"] = source_data["total_ballots"]
    chart_data["latest_ballots_added"] = source_data["ballots_added"]

    new_race_wide_update = {
        'reporting_time': source_data["reporting_time"],
        'total_ballots': source_data["total_ballots"],
        'ballots_added': source_data["ballots_added"],
    }

    chart_data["updates"]["race_wide"].append(new_race_wide_update)
    chart_data["updates"]["race_wide"].sort(
        key=lambda x: x['reporting_time'], reverse=True
    )
    
    for c in source_data['candidates']:
        c['reporting_time'] = source_data["reporting_time"]

    chart_data["updates"]["per_candidate"].extend(source_data['candidates'])
    chart_data["updates"]["per_candidate"].sort(
        key=lambda x: x['reporting_time'], reverse=True
    )

    return chart_data


def compile_chart_data(path):
    if 'bar-charts' in path:
        bar_chart_data = compile_bar_chart_data(path)
        bar_chart_json = json.dumps(bar_chart_data)
        s3.archive(bar_chart_json, path=path)
    elif 'line-charts' in path:
        line_chart_data = compile_line_chart_data(path)
        line_chart_json = json.dumps(line_chart_data)
        s3.archive(line_chart_json, path=path)


def main(path=None):
    if path:
        compile_chart_data(path)
    else:
        for path in CHART_METADATA:
            compile_chart_data(path)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-p',
        '--path',
        type=str,
    )

    args = parser.parse_args()

    main(args.path)
