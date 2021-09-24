import json
import layout, analyzer
import termcolor as tmc
from typing import Dict, List

JSON = Dict[str, any]


def print_color(item: JSON, dtype: str, data: List):
    percent = 0
    for result in data:
        if item['data'][dtype] > result['data'][dtype]:
            percent += 1
    percent /= len(data)

    string = "{:.2%}".format(item['data'][dtype]).rjust(6, ' ') + '  '
    if percent > .9:
        return '\033[38;5;46m' + string + '\033[0m' # bright green
    elif percent > .7:
        return '\033[38;5;2m' + string + '\033[0m' # green

    elif percent < .1:
        return '\033[38;5;9m' + string + '\033[0m' # bright red
    elif percent < .3:
        return '\033[38;5;124m' + string + '\033[0m' # red
    else:
        return '\033[38;5;250m' + string + '\033[0m'


def get_results(filename: str, thumb: str='LT'):
    layouts = layout.load_dir('layouts')
    data = json.load(open(filename, 'r'))

    results = {
        'file': filename,
        'sort': 'name',
        'data': []
    }

    for keys in layouts:
        counts = analyzer.count_trigrams(keys, data, thumb)
        results['data'].append(
            {
                'name': keys['name'],
                'data': counts,
            }
        )

    sort_results(results, 'name', high=False)
    return results


def sort_results(results: List[dict], sort: str, high: bool=True):

    results['sort'] = sort
    if (sort == 'name'):
        results['data'] = sorted(results['data'], key=lambda x : x['name'].lower(), reverse=high)
    else:
        results['data'] = sorted(results['data'], key=lambda x : x['data'][sort], reverse=high)

    return results
         


def show_results(results: List[dict]):
    print(results['file'].upper())
    print(
        ("sort by " + results['sort'].upper() + ":").ljust(22, ' '), 
        'alternate'.rjust(8, ' '),
        'roll'.rjust(8, ' '),
        'redirect'.rjust(8, ' '),
        'onehand'.rjust(8, ' '),
        'sfb'.rjust(8, ' '),
        'dsfb'.rjust(8, ' '),
        # 'sfT'.rjust(8, ' '),
        # 'sfR'.rjust(8, ' '),
    )
    for item in results['data']:
        print(
            (item['name'] + '\033[38;5;250m' + ' ').ljust(36, '-') + '\033[0m', 
            print_color(item, 'alternate', results['data']),
            print_color(item, 'roll', results['data']),
            print_color(item, 'redirect', results['data']),
            print_color(item, 'onehand', results['data']),
            print_color(item, 'sfb', results['data']),
            print_color(item, 'dsfb', results['data']),
            # print_color(item, 'sfT', results['data']),
            # print_color(item, 'sfR', results['data']),
        )


if __name__ == "__main__":
    results = get_results('data/200-data.json')
    #results = sort_results(results, 'redirect')
    show_results(results)