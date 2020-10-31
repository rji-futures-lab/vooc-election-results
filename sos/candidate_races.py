from random import randint

from graphics import compile_bar_chart_data, compile_line_chart_data
import s3


def get_endpoints():
    with open('sos-endpoints.txt') as f:
        return [l.strip() for l in f.readlines()]


def get_current_results(endpoint):
    url = f"https://api.sos.ca.gov/returns/{endpoint}"
    r = requests.get(url)
    r.raise_for_status()

    return r.content


def main():
    for e in get_endpoints():

        current_results = get_current_results(e)
    
        try:
            cached_results = get_cached_results(e)
        except S3_CLIENT.exceptions.NoSuchKey:
            has_diffs = True
        else:
            has_diffs = current_results != cached_results
        
        if has_diffs:
            cache_results(e, current_results)
            print(f"New results cached for {e}")
        else:
            print(f"No update for {e}")

        sleep(3)


if __name__ == '__main__':
    main()
