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
        "themedir": "themes",
        "theme": "festive",
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
        },
        "layouts": {}
    }

    layouts = layout.load_dir(config['layoutdir'])
    for keys in layouts:
        config['layouts'][keys['name'].lower()] = True

    return config


def get_color(item: JSON, dtype: str, data: List):
    percent = 0
    for result in data:
        if item['data'][dtype] > result['data'][dtype]:
            percent += 1
    percent /= len(data)

    colors = json.load(open(config['themedir'] + "/" + config['theme'] + ".json"))['colors']

    string = "{:.2%}".format(item['data'][dtype]).rjust(6, ' ') + '  '
    if percent > .9:
        return '\033[38;5;' + colors['highest'] + 'm' + string + '\033[0m'
    elif percent > .7:
        return '\033[38;5;' + colors['high'] + 'm' + string + '\033[0m'

    elif percent < .1:
        return '\033[38;5;' + colors['lowest'] + 'm' + string + '\033[0m'
    elif percent < .3:
        return '\033[38;5;' + colors['low'] + 'm' + string + '\033[0m'
    else:
        return '\033[38;5;' + colors['base'] + 'm' + string + '\033[0m'


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
    print("thumb:", config['thumb-space'])
    print(("sort by " + results['sort'].upper() + ":").ljust(22, ' '), end=' ')

    for trigram_type in config['columns']:
        if config['columns'][trigram_type]:
            print(trigram_type.rjust(8, ' '), end=' ')
    print()

    for item in results['data']:
        if not config['layouts'][item['name'].lower()]:
            continue

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

        # toggle columns/layouts as visible or not
        if sys.argv[1] in ['toggle', 'tg']:
            if len(sys.argv) != 4:
                if len(sys.argv) == 3 and sys.argv[2] == 'c':
                    print("usage: ./" + sys.argv[0] + " toggle c [column]")
                    exit()
                elif len(sys.argv) == 3 and sys.argv[2] == 'l':
                    print("usage: ./" + sys.argv[0] + " toggle l [layout]")
                    exit()
                else:
                    print("usage: ./" + sys.argv[0] + " toggle c/l [column/layout]")
                    exit()

            if sys.argv[2] in ['column', 'c']:
                if sys.argv[3] in ['all', 'a']:
                    if True in config['columns'].values():
                        new_state = False
                    else:
                        new_state = True

                    for column in config['columns']:
                        config['columns'][column] = new_state
                elif sys.argv[3] in config['columns']:
                    config['columns'][sys.argv[3]] = not config['columns'][sys.argv[3]]
                else:
                    print("[" + sys.argv[3] + "] is not a valid column name")
                    exit()
            elif sys.argv[2] in ['layout', 'l']:
                if sys.argv[3] in ['all', 'a']:
                    if True in config['layouts'].values():
                        new_state = False
                    else:
                        new_state = True

                    for keys in config['layouts']:
                        config['layouts'][keys] = new_state
                elif sys.argv[3] in config['layouts']:
                    config['layouts'][sys.argv[3]] = not config['layouts'][sys.argv[3]]
                else:
                    print("[" + sys.argv[3] + "] is not a valid layout name")
                    exit()
            else:
                print("usage: ./" + sys.argv[0] + " toggle c/l [column/layout]")
                exit()
        
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
                print("usage: ./" + sys.argv[0] + " thumb [LT/RT/NONE]")
                exit()

            if not sys.argv[2].upper() in ['LT', 'RT', 'NONE']:
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

        elif sys.argv[1] in ['reset']:
            config = init_config()

        elif sys.argv[1] in ['help', 'hp', 'h', '?']:
            print("Usage:", sys.argv[0], "[command]", "[arg]", "\n") 
            print(
                "   ",
                "sort (st)".rjust(15, ' '), 
                "[column] {high/low}".rjust(22, ' '), 
                "order the list of layouts based on a column".rjust(45, ' '),
                "\n"
            )
            print(
                "   ",
                "toggle c (tg c)".rjust(15, ' '),
                "[column/all]".rjust(22, ' '), 
                "turn on/off the visibility of a column".rjust(45, ' '),
                "\n"
            )
            print(
                "   ",
                "toggle l (tg l)".rjust(15, ' '),
                "[layout/all]".rjust(22, ' '), 
                "turn on/off the visibility of a layout".rjust(45, ' '),
                "\n"
            )
            print(
                "   ",
                "data (dt)".rjust(15, ' '), 
                "[path/to/file]".rjust(22, ' '), 
                "set the data to use for the analysis".rjust(45, ' '),
                "\n"
            )
            print(
                "   ",
                "thumb (tb)".rjust(15, ' '), 
                "[LT/RT/NONE]".rjust(22, ' '),
                "change which thumb is used for space".rjust(45, ' '),
                "\n"
            )
            print(
                "   ",
                "reset".rjust(15, ' '), 
                "[]".rjust(22, ' '),
                "set the config to its default settings".rjust(45, ' '),
                "\n"
            )

            exit()

        else:
            print(
                "[" + sys.argv[1] + 
                "] is not a valid command, type ./" + 
                sys.argv[0] + 
                " help for a list of commands"
            )
            exit()

    results = get_results(config)
    show_results(results, config)

    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))