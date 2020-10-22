import xml.etree.ElementTree as et
import requests
import json
import random

from function import *

def parse_single(xml, race_id, output_path):
    try:
        old_results = json.loads(get_cached_results(f'{output_path}/latest.json'))
    except Exception as e:
        old_results = None
        print(e)

    root = et.fromstring(xml)
    xpath = './Table[RaceID="' + str(race_id) + '"]'
    
    elements = root.findall(xpath)
    candidates = [{c.tag: c.text for c in list(e)} for e in elements]

    data = json.loads('{"totalVotes": 0, "ReportingTime": "", "candidates": []}')
    data['ReportingTime'] = root.find('GeneratedDate').text

    for candidate in candidates:
        item = {
            'Name': candidate['ContestantName'],
            'Party': candidate['Party'],
            'Votes': candidate['TotalVotes'],
            'Percent': candidate['ContestantVotePercent'],
            'Incumbent': False
        }

        data['totalVotes'] += int(item['Votes'])
        data['votesAdded'] = data['totalVotes'] - old_results['totalVotes'] if old_results else data['totalVotes']
        data['candidates'].append(item)

    data = json.dumps(data)

    write_to_s3(f'{output_path}/latest.json', data, 'application/json')
    write_to_s3(f'{output_path}/{json.loads(data)["ReportingTime"]}.json', data, 'application/json')

def parse_sd(xml):
    try:
        old_results = json.loads(get_cached_results('latest.json'))
    except Exception as e:
        print(e)

    data = json.loads('{"generatedDate": "", "source": "SD"}')

    root = et.fromstring(xml)
    data['generatedDate'] = root.find('GeneratedDate').text
    elements = root.findall('./Table')

    races_list = [{c.tag: c.text for c in list(e)} for e in elements]

    current_id = '0'
    for race in races_list:

        if str(race['RaceID']) == current_id:
            candidate = {
                'name': race['ContestantName'],
                'party': race['Party'],
                'isIncumbent': False,
                'totalVotes': race['TotalVotes'],
                'contestantVotePercent': race['ContestantVotePercent']
            }
            data[current_id]['totalBallots'] += int(race['TotalVotes'])
            data[current_id]['ballotsAdded'] = data[current_id]['totalBallots'] - old_results[current_id]['totalBallots']
            data[current_id]['contestants'][race['ContestantID']] = candidate

        else:
            current_id = str(race['RaceID'])
            item = {str(race['RaceID']):
                {
                    'raceName': race['RaceName'],
                    'ballotsAdded': 0,
                    'totalBallots': 0,
                    'contestants': {
                        race['ContestantID']: {
                            'name': race['ContestantName'],
                            'party': race['Party'],
                            'isIncumbent': False,
                            'totalVotes': race['TotalVotes'],
                            'contestantVotePercent': race['ContestantVotePercent']
                        }
                    }
                }
            }
            item[str(race['RaceID'])]['totalBallots'] += int(race['TotalVotes'])
            item[str(race['RaceID'])]['ballotsAdded'] = item[str(race['RaceID'])]['totalBallots'] - old_results[current_id]['totalBallots']
            data.update(item)

    with open('data/sd/output/output.json', 'w') as f:
        json.dump(data, f)

    return json.dumps(data)

def simulate(url, trials):
    i = 1
    root = et.fromstring(requests.get(url).content)

    max_voter_turnout = random.uniform(0.7, 0.8) * int(root.find('RegisteredVoters').text)
    avg_votes_per_precinct = max_voter_turnout / 1414
    
    while i <= trials:
        elements = root.findall('./Table')

        candidate = 1
        num_candidates = 0
        current_id = '0'
        for table in elements:
            total_votes = round(random.uniform(avg_votes_per_precinct*int(table.find('NumberOfPrec').text)*0.22*i, avg_votes_per_precinct*int(table.find('NumberOfPrec').text)*0.25*i))

            if current_id == table.find('RaceID'):
                table.find('TotalVotes').text = str(vote_distribution[candidate])
                table.find('ContestantVotePercent').text = str(vote_distribution[candidate]/total_votes*100)[0:4]
                candidate += 1
            else:
                current_id = table.find('RaceID').text
                candidate = 0

                xpath = './/*[RaceID="' + str(current_id) + '"]' 
                num_candidates = len(root.findall(xpath))
                
                j = 0
                k = 0
                vote_distribution = []
                distribution_total = 0
                while j < num_candidates:
                    vote_distribution.append(random.uniform(0, 1))
                    distribution_total += vote_distribution[j]
                    j += 1
                while k < num_candidates:
                    vote_distribution[k] = round((vote_distribution[k] / distribution_total) * total_votes)
                    distribution_total += vote_distribution[k]
                    k += 1

                table.find('TotalVotes').text = str(vote_distribution[0])
                table.find('ContestantVotePercent').text = str(vote_distribution[0]/total_votes*100)[0:4]

        file = "data/sd/input/test" + str(i) + ".xml"
        with open(file, 'w') as f:
            f.write(et.tostring(root, encoding='unicode'))

        data = parse_sd(et.tostring(root, encoding='unicode'))

        write_to_s3(f'test{i}.json', data, 'json')
        write_to_s3(f'latest.json', data, 'json')

        i += 1

def main():
    url = 'http://www.livevoterturnout.com/sandiego/liveresults/summary_10.xml'
    parse_single(requests.get(url).content, 2, 'sd/us-rep/district/49')
    # data = parse_sd(requests.get(url).content)
    # write_to_s3(f'latest.json', data, 'json')
    # write_to_s3(f'{json.loads(data)["generatedDate"]}.json', data, 'json')
    # simulate(url, 4)

def lambda_handler(event, context):
    main()

if __name__ == '__main__':
    main()
