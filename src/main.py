import sys
import os
import json
import layout, analyzer
import termcolor as tmc
from typing import Dict, List

JSON = Dict[str, any]


def init_config():
    config = {
        "layoutdir": "layouts",
        "datafile": "data/200-data.json",
        "thumb-space": "LT",
        "sort": "name",
        "sort-high": False,
        "columns": {
            "alternate": True,
            "roll": True,
            "redirect": True,
            "onehand": True,
            "sfb": True,
            "dsfb": True,
            "sfT": False,
            "sfR": False
        }
    }
    
    return config


def get_color(item: JSON, dtype: str, data: List):
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


def get_results(config: JSON):
    layouts = layout.load_dir(config['layoutdir'])
    data = json.load(open(config['datafile'], 'r'))

    results = {
        'file': data['file'],
        'sort': 'name',
        'data': []
    }

    for keys in layouts:
        counts = analyzer.count_trigrams(keys, data, config['thumb-space'])
        results['data'].append(
            {
                'name': keys['name'],
                'data': counts,
            }
        )

    sort_results(results, config)
    return results


def sort_results(results: List[dict], config: JSON):

    results['sort'] = config['sort']
    if (config['sort'] == 'name'):
        results['data'] = sorted(results['data'], key=lambda x : x['name'].lower(), reverse=config['sort-high'])
    else:
        results['data'] = sorted(results['data'], key=lambda x : x['data'][config['sort']], reverse=config['sort-high'])

    return results


def show_results(results: List[dict], config: JSON):

    print(results['file'].upper())
    print(("sort by " + results['sort'].upper() + ":").ljust(22, ' '), end=' ')

    for trigram_type in config['columns']:
        if config['columns'][trigram_type]:
            print(trigram_type.rjust(8, ' '), end=' ')
    print()

    for item in results['data']:
        print((item['name'] + '\033[38;5;250m' + ' ').ljust(36, '-') + '\033[0m', end=' ')
        for trigram_type in config['columns']:
            if config['columns'][trigram_type]:
                print(get_color(item, trigram_type, results['data']), end=' ')
        print()


if __name__ == "__main__":
    
    try:
        config = json.load(open('config.json', 'r'))
    except FileNotFoundError:
        config = init_config()

    if len(sys.argv) > 1:

        # toggle columns as visible or not
        if sys.argv[1] in ['toggle', 'tg']:
            if len(sys.argv) != 3:
                print("usage: ./" + sys.argv[0] + " toggle [column]")
                exit()

            if not sys.argv[2] in config['columns']:
                print("[" + sys.argv[2] + "] is not a valid column name")
                exit()

            config['columns'][sys.argv[2]] = not config['columns'][sys.argv[2]]
        
        elif sys.argv[1] in ['sort', 'st']:
            if not 2 < len(sys.argv) < 5:
                print("usage: ./" + sys.argv[0] + " sort [column] {high/low}")
                exit()

            if not (
                sys.argv[2] in config['columns'] or 
                sys.argv[2] == 'name' or
                sys.argv[2] in ['high', 'low']
            ):
                print("[" + sys.argv[2] + "] is not a valid column name")
                exit()

            if len(sys.argv) == 4 and not sys.argv[3] in ['high', 'low']:
                print("[" + sys.argv[3] + "] is not a valid sort direction")
                exit()

            if sys.argv[2] == 'high':
                config['sort-high'] = True
            elif sys.argv[2] == 'low':
                config['sort-high'] = False
            else:
                config['sort'] = sys.argv[2]

            if len(sys.argv) == 4:
                if sys.argv[3] == 'high':
                    config['sort-high'] = True
                else:
                    config['sort-high'] = False

            if sys.argv[2] == 'name' and len(sys.argv) != 4:
                config['sort-high'] = False
        
        elif sys.argv[1] in ['thumb', 'tb']:
            if len(sys.argv) != 3:
                print("usage: ./" + sys.argv[0] + " thumb [LT/RT]")
                exit()

            if not sys.argv[2].upper() in ['LT', 'RT']:
                print("[" + sys.argv[2] + "] is not a valid thumb name")
                exit()

            config['thumb-space'] = sys.argv[2].upper()

        elif sys.argv[1] in ['data', 'dt']:
            if len(sys.argv) != 3:
                print("usage: ./" + sys.argv[0] + " data [path/to/file]")
                exit()

            if not os.path.isfile(sys.argv[2]):
                print("[" + sys.argv[2] + "] is not a valid filename")
                exit()

            config['datafile'] = sys.argv[2]

    results = get_results(config)
    show_results(results, config)

    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))