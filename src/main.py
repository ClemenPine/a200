import sys
import os
import json
import copy
import layout, analyzer, config, parser
from typing import Dict, List

JSON = Dict[str, any]


def get_layout_percent(item: JSON, metric: str, results: JSON):

    wins = 0
    item_metric = item['metrics'][metric]

    for result in results['data']:
        result_metric = result['metrics'][metric]

        if item_metric > result_metric:
            wins += 1
        
    percent = wins / len(results['data'])
    return percent


def color(item: JSON, metric: str, data: JSON, conf: JSON, isPercent: bool=True):

    # get percentage of layouts worse
    percent = get_layout_percent(item, metric, data)

    # get string
    value = item['metrics'][metric]
    if isPercent:
        string = f'{value:>6.2%}  '
    else:
        string = f'{value:>6.2f}  '    

    # get theme
    colors = config.get_colors(conf)

    # determine color 
    if percent > .9:
        color_idx = colors['highest']
    elif percent > .7:
        color_idx = colors['high']
    elif percent < .1:
        color_idx = colors['lowest']
    elif percent < .3:
        color_idx = colors['low']
    else:
        color_idx =  colors['base']

    # printing
    reg_color = '\033[0m'
    color = f'\033[38;5;{color_idx}m'

    return color + string + reg_color


def get_results(conf: JSON):

    cache_path = os.path.join(conf['cachedir'], 'cached-' + conf['datafile'] + '.json')
    data_path = os.path.join(conf['datadir'], conf['datafile'] + '.json')

    # create cache dir if one isn't available
    if not os.path.isdir(conf['cachedir']):
        os.mkdir(conf['cachedir'])

    # create cache or load empty one
    if os.path.isfile(cache_path):

        with open(cache_path, 'r') as f:
            cache = json.load(f)
    else:   
        cache = {
            'file': conf['datafile'],
            'data': {}
        }

    # load data
    with open(data_path, 'r') as f:
        data = json.load(f)

    results = {
        'file': data['file'],
        'data': []
    }

    layouts = layout.load_dir(conf['layoutdir'])
    for keys in layouts:
        item = {
            'name': keys['name'],
            'file': keys['file'],
            'sort': 0,
            'metrics': {},
        }

        # add key if it doesn't exist or contains a hash mismatch
        if (
            not keys['name'] in cache['data'] or
            keys['hash'] != cache['data'][keys['name']]['hash']
        ):
            cache['data'][keys['name']] = {
                'hash': keys['hash']
            }

        # get stats
        if not conf['thumb-space'] in cache['data'][item['name']]:
            cache['data'][item['name']][conf['thumb-space']] = analyzer.get_results(keys, data, conf)

        item['metrics'] = cache['data'][item['name']][conf['thumb-space']]
    
        results['data'].append(item)
        
    sort_results(results, conf)

    # write cache
    with open(cache_path, 'w') as f:
        f.write(json.dumps(cache, indent=4)) 

    return results


def sort_results(results: JSON, conf: JSON):

    # calulate sort criteria
    for item in results['data']:
        for sort in conf['sort']:
            percent = get_layout_percent(item, sort, results)
            if str(conf['sort'][sort])[0] == '-':
                value = 1 - percent
            else:
                value = percent

            item['sort'] += value * abs(conf['sort'][sort])

    # sort
    if conf['sort'] == 'name':
        results['data'] = sorted(results['data'], key=lambda x : x['name'].lower(), reverse=conf['sort-high'])
    else:
        results['data'] = sorted(results['data'], key=lambda x : x['sort'], reverse=conf['sort-high'])


def show_results(results: JSON, conf: JSON):

    # print metadata
    print(results['file'].upper())

    if conf['filter']:
        print('filter by:  ', end='')

        for filter, val in conf['filter'].items():
            print(f'{filter} {val:.2%}  ', end='')
        print()

    if conf['sort']:
        print('sort by:  ', end='')

        for sort, val in conf['sort'].items():
            print(f'{sort} {val:.0%}  ', end='')
        print()

    print(f'thumb: {conf["thumb-space"]:<16}', end='')

    # print column names
    for metric, value in flatten(conf['columns']).items():
        if value:
            print(f'{metric:>8} ',end='')
    print()

    # get filters
    filters = []
    for name, val in conf['filter'].items():

        filter = {
            'name': name,
            'dir': val // abs(val),
            'cutoff': abs(val)
        }

        filters.append(filter)

    # print rows
    for item in results['data']:
        layout_name = item['name'].lower()

        # enable new layouts by default
        if layout_name not in conf['layouts']:
            conf['layouts'][layout_name] = True

        # ignore hidden layouts 
        if not conf['layouts'][layout_name]:
            continue

        # ignore filter layouts
        for filter in filters:
            name = filter['name']
            dir = filter['dir']
            cutoff = filter['cutoff']

            if dir*(item['metrics'][name] - cutoff) < 0:
                break
        else:
            # print layout stats
            print((layout_name + '\033[38;5;250m' + ' ').ljust(36, '-') + '\033[0m', end=' ')
            for metric, value in flatten(conf['columns']).items():
                if value:
                    print(color(item, metric, results, conf, metric not in ['roll-rt', 'oneh-rt']), end=' ')
            print()


def print_layout(results: JSON, conf: JSON):

    print(results['file'].upper())
    print(f'thumb: {conf["thumb-space"]}')

    layouts = [item for item in results['data'] if conf['layouts'][item['name'].lower()] == True]
    for item in layouts:

        # calculate colors
        cl = {}
        for metric in item['metrics']:
            cl[metric] = color(item, metric, results, conf)

        print()

        # header
        print(item['name'])
        layout.pretty_print(item['file'], conf)
        print()

        print('Trigrams')
        print('========')
        print(f'{"Alternates -":>12} Total: {cl["alternate"]}')
        print(f'{"Rolls -":>12} Total: {cl["roll"]} In: {cl["roll-in"]} Out: {cl["roll-out"]} Ratio: {cl["roll-rt"]}')
        print(f'{"Onehands -":>12} Total: {cl["onehand"]} In: {cl["oneh-in"]} Out: {cl["oneh-out"]} Ratio: {cl["oneh-rt"]}')
        print(f'{"Redirects -":>12} Total: {cl["redirect"]}')

        if item['metrics']['unknown'] > 0:
            print(f'{"Unknown -":>12} Total: {cl["unknown"]}')
        print()

        print('Same Finger')
        print('===========')
        print(f'{"SFB -":>12}{cl["sfb"]} {"DSFB -":>12}{cl["dsfb"]}')
        print(f'{"SFT -":>12}{cl["sfT"]} {"SFR -":>12}{cl["sfR"]}')
        print()

        print("Finger Use")
        print("==========")
        print(f'{"Left -":>12} Total: {cl["LTotal"]} ', end='')
        for finger in ['LP', 'LR', 'LM', 'LI']:
            print(f'{finger}: {cl[finger]} ', end='')
        print()

        print(f'{"Right -":>12} Total: {cl["RTotal"]} ', end='')
        for finger in ['RP', 'RR', 'RM', 'RI']:
            print(f'{finger}: {cl[finger]} ', end='')
        print()

        if (conf['thumb-space'] != 'NONE'):
            print(f'{"Thumb -":>12} Total: {cl["TB"]}')
        print()

        print("Row Use")
        print("=======")
        print(f'{"Top -":>12} {cl["top"]}{"Home -":>12} {cl["home"]}{"Bottom -":>12} {cl["bottom"]}')


def flatten(section: JSON):

    res = {}
    for item in section:
        if type(section[item]) == bool:
            res[item] = section[item]
        else:
            res.update(flatten(section[item]))

    return res


if __name__ == "__main__":

    conf = parser.parse_args(*sys.argv)

    if conf['single-mode']['active']:
        layout_conf = copy.deepcopy(conf)
        layout_conf['layouts'] = {item: False for item in layout_conf['layouts']}

        for layout_name in layout_conf['single-mode']['layouts']:
            layout_conf['layouts'][layout_name] = True
    
        results = get_results(layout_conf)
        print_layout(results, layout_conf)
    else:
        results = get_results(conf)
        show_results(results, conf)

    config.write(conf, path='config.json')