import json

import s3


def get_previous_total_ballots(race_id):
    previous_data = s3.read_from(f"bar-charts/{race_id}/latest.json")

    if previous_data:
        as_dict = json.loads(previous_data)
        previous_total_ballots = as_dict['total_ballots']
    else:
        previous_total_ballots = 0

    return previous_total_ballots


def get_race_meta_data(race_id):
    with open("races.json") as f:
        race_meta_data = json.loads(f.read())

    return race_meta_data[race_id]


def compile_bar_chart_data(race_id, race_data, reporting_time):

    race_meta_data = get_race_meta_data(race_id)
    candidates_meta_data = race_meta_data['candidates']

    candidates = []

    for c_id, c_data in race_data.items():
        candidate_data = candidates_meta_data[c_id]
        candidate_data["votes"] = int(c_data["TotalVotes"]) 
        candidates.append(candidate_data) 

    previous_total_ballots = get_previous_total_ballots(race_id)
    total_ballots = sum([c["votes"] for c in candidates])

    candidate_image_count = 0

    for candidate in candidates:
        candidate["percent"] = round((candidate["votes"] / total_ballots) * 100, 2)

        if candidate['img_url']:
            candidate_image_count += 1

    data_dict = {
        "race_title": race_meta_data["race_title"],
        "reporting_time": reporting_time,
        "total_ballots": total_ballots,
        "ballots_added": total_ballots - previous_total_ballots,
        "use_candidate_images": candidate_image_count == len(candidates),
        "candidates": candidates,
    }

    if 'description' in race_meta_data:
        data_dict['description'] = race_meta_data['description']

    return data_dict


def compile_line_chart_data(race_id):
    
    previous_data = s3.read_from(f"line-charts/{race_id}/latest.json")
    race_meta_data = get_race_meta_data(race_id)

    if previous_data:
        data_dict = json.loads(previous_data)
    else:
        data_dict = {
            "race_title": race_meta_data["race_title"],
            "latest_reporting_time": "",
            "latest_total_ballots": 0,
            "latest_ballots_added": 0,
            "updates": []
        }

    if 'description' in race_meta_data:
        data_dict['description'] = race_meta_data['description']

    latest_bar_graph_data = json.loads(s3.read_from(f"bar-charts/{race_id}/latest.json"))

    data_dict["latest_reporting_time"] = latest_bar_graph_data["reporting_time"]
    data_dict["latest_total_ballots"] = latest_bar_graph_data["total_ballots"]
    data_dict["latest_ballots_added"] = latest_bar_graph_data["ballots_added"]
    
    data_dict["updates"].append(latest_bar_graph_data)
    data_dict["updates"].sort(key=lambda x: x['reporting_time'], reverse=True)

    assert len(data_dict["updates"]) > 1

    return data_dict
