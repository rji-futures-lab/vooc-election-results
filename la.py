from itertools import groupby
import json
import xml.etree.ElementTree as et

import requests

import s3


def get_results():
    url = "https://rrcc.co.la.ca.us/results/results-06037-2020-11-03.xml"
    r = requests.get(url)
    r.raise_for_status()

    return r.headers['content-type'], r.content


def parse_element(element):

    tag = element.tag.strip()
    text = element.text.strip()
    children = list(element)

    child_elements = list(element)

    # if len(child_elements) == 0:
    #     return element.text
    # else:
    #     i


def parse_results(xml):
    root = et.fromstring(xml)

    reporting_time = root.find('GeneratedDate').text

    results = [
        {c.tag: c.text for c in list(table)}
        for table in root.findall('./Table')
    ]

    return reporting_time, results


def main():
    content_type, results = get_results()

    results_updated = s3.archive(
        results, content_type=content_type, path='la/orig'
    )

    if results_updated:
        reporting_time, parsed_results = parse_results(results)


if __name__ == '__main__':
    main()
