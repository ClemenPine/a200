import sys
import os
import json
import layout, analyzer
from typing import Dict, List

JSON = Dict[str, any]


def init_config():
    
    if os.path.isfile('init-config.json'):
        config = json.load(open('init-config.json', 'r'))
    else:
        config = json.load(open(os.path.join('src', 'static', 'config-init.json'), 'r'))
    layouts = layout.load_dir(config['layoutdir'])

    for keys in layouts:
        config['layouts'][keys['name'].lower()] = True

    return config


def get_layout_percent(item: JSON, metric: str, results: JSON):

    wins = 0
    for result in results['data']:
        if item['metrics'][metric] > result['metrics'][metric]:
            wins += 1
    return wins / len(results['data'])


def print_color(item: JSON, metric: str, data: JSON):

    # get percentage of layouts worse
    percent = get_layout_percent(item, metric, data)

    # get string
    string = "{:.2%}".format(item['metrics'][metric]).rjust(6, ' ') + '  '

    # color printing based on percentage
    colors = json.load(open(os.path.join(config['themedir'], config['theme'] + '.json'), 'r'))['colors']
    if percent > .9:
        print('\033[38;5;' + colors['highest'] + 'm' + string + '\033[0m', end=' ')
    elif percent > .7:
        print('\033[38;5;' + colors['high'] + 'm' + string + '\033[0m', end=' ')

    elif percent < .1:
        print('\033[38;5;' + colors['lowest'] + 'm' + string + '\033[0m', end=' ')
    elif percent < .3:
        print('\033[38;5;' + colors['low'] + 'm' + string + '\033[0m', end=' ')
    else:
        print('\033[38;5;' + colors['base'] + 'm' + string + '\033[0m', end=' ')


def get_results(config: JSON):

    # open/create results cache
    cachefile = os.path.join(config['cachedir'], 'cached-' + config['datafile'] + '.json')

    if not os.path.isdir(config['cachedir']):
        os.mkdir(config['cachedir'])

    if os.path.isfile(cachefile):
        cache = json.load(open(cachefile, 'r'))
    else:   
        cache = {
            'file': config['datafile'],
            'data': {}
        }

    layouts = layout.load_dir(config['layoutdir'])
    data = json.load(open(os.path.join(config['datadir'], config['datafile'] + '.json'), 'r'))

    results = {
        'file': data['file'],
        'data': []
    }

    for keys in layouts:
        item = {
            'name': keys['name'],
            'sort': 0,
            'metrics': {},
        }

        # add key if it doesn't exist or contains a hash mismatch
        if (
            not keys['name'] in cache['data'] or
            keys['hash'] != cache['data'][keys['name']]['hash']
        ):
            cache['data'][keys['name']] = {
                'hash': keys['hash'],
                'trigrams': {}
            }

        # get stats
        if not config['thumb-space'] in cache['data'][item['name']]:
            cache['data'][item['name']][config['thumb-space']] = analyzer.get_results(keys, data, config)

        item['metrics'] = cache['data'][item['name']][config['thumb-space']]
    
        results['data'].append(item)
        
    sort_results(results, config)

    # write cache
    with open(cachefile, 'w') as f:
        f.write(json.dumps(cache, indent=4)) 

    return results


def sort_results(results: JSON, config: JSON):

    # calulate sort criteria
    for item in results['data']:
        for sort in config['sort']:
            percent = get_layout_percent(item, sort, results)
            if str(config['sort'][sort])[0] == '-':
                value = 1 - percent
            else:
                value = percent

            item['sort'] += value * abs(config['sort'][sort])

    # sort
    if config['sort'] == 'name':
        results['data'] = sorted(results['data'], key=lambda x : x['name'].lower(), reverse=config['sort-high'])
    else:
        results['data'] = sorted(results['data'], key=lambda x : x['sort'], reverse=config['sort-high'])


def show_results(results: JSON, config: JSON):

    # print metadata
    print(results['file'].upper())
    print("sort by:", end='   ')
    for sort in config['sort']:
        print(
            sort, 
            "{:.0%}".format(config['sort'][sort]),
            end='   '
        )
    print()

    # print(("sort by " + config['sort'].upper() + ":").ljust(22, ' '), end=' ')
    print(("thumb: " + config['thumb-space']).ljust(22, ' '), end=' ')


    # print column names
    for metric, value in flatten(config['columns']).items():
        if value:
            print(metric.rjust(8, ' '), end=' ')
    print()

    # print rows
    for item in results['data']:

        # ignore hidden layouts 
        if not config['layouts'][item['name'].lower()]:
            continue

        # print layout stats
        print((item['name'] + '\033[38;5;250m' + ' ').ljust(36, '-') + '\033[0m', end=' ')
        for metric, value in flatten(config['columns']).items():
            if value:
                print_color(item, metric, results)
        print()


def flatten(section: JSON):

    res = {}
    for item in section:
        if type(section[item]) == bool:
            res[item] = section[item]
        else:
            res.update(flatten(section[item]))

    return res
        

def get_states(section: JSON):

    if type(section) == bool:
        return [section]

    states = []
    for item in section:
        states += get_states(section[item])

    return states


def find_section(section: JSON, target: str):

    if type(section) != dict:
        return []

    matches = []
    for item in section:
        if item == target:
            matches.append(section)
        
        matches += find_section(section[item], target)

    return matches


def set_states(section: JSON, new_state: bool):

    for item in section:
        if type(section[item]) == bool:
            section[item] = new_state
        else:
            set_states(section[item], new_state)


def parse_args(name='', action=None, *args):

    # open/init config
    try:
        config = json.load(open('config.json', 'r'))
    except FileNotFoundError:
        config = init_config()

    # parse args
    if action in ['toggle', 'tg', 'tc', 'tl']:

        # parse target and axis
        if action in ['toggle', 'tg']:
            if args[0] in ['column', 'c']:
                axis = 'columns'
            elif args[0] in ['layout', 'l']:
                axis = 'layouts'
            targets = args[1:] 
        else:
            if action == 'tc':
                axis = 'columns'
            elif action == 'tl':
                axis = 'layouts'
            targets = args[0:]

        # recursively find and set states for each target
        for target in targets:
            if axis == 'layouts':
                target = target.lower()

            if target in ['all', 'a']:
                set_states(config[axis], not True in get_states(config[axis]))
            else:
                section = find_section(config[axis], target)[0]
                if type(section[target]) == bool:
                    section[target] = not section[target]
                else:
                    set_states(section[target], not True in get_states(section[target]))

    elif action in ['sort', 'st']:

        config['sort'] = {}

        count = 0
        total_percent = 0

        for arg in args:
            # sorting direction
            if arg in ['high', 'h']:
                config['sort-high'] = True
            elif arg in ['low', 'l']:
                config['sort-high'] = False
            # parse metric string
            else:
                if not '%' in arg:
                    if '-' in arg:
                        arg = ('-', arg[1:])
                    else:
                        arg = ('', arg)
                    count += 1
                else:
                    arg = arg.split('%')
                    total_percent += abs(float(arg[0]))

                config['sort'][arg[1]] = arg[0]

        # calculate percent per unassigned metric
        if count:
            percent_left = (100 - total_percent) / count
        else:
            percent_left = 0
        
        # allocate percents and convert to float
        for item in config['sort']:
            if config['sort'][item] in ['', '-']:
                config['sort'][item] += str(percent_left)
            config['sort'][item] = float(config['sort'][item]) / 100

    elif action in ['thumb', 'tb']:
        
        if args[0].upper() in ['LT', 'RT', 'NONE', 'AVG']:
            config['thumb-space'] = args[0].upper()

    elif action in ['data', 'dt']:
        
        if os.path.isfile(os.path.join(config['datadir'], args[0] + '.json')):
            config['datafile'] = args[0]

    elif action in ['theme', 'tm']:

        if os.path.isfile(os.path.join(config['themedir'], args[0] + '.json')):
            config['theme'] = args[0]

    elif action in ['reset']:
        
        config = init_config()

    elif action in ['config', 'cs', 'cl']:

        if action in ['config', 'cg']:
            if args[0] in ['save', 's']:
                command = 'save'
                filename = args[1]
            elif args[0] in ['load', 'l']:
                command = 'load'
                filename = args[1]

        elif action == 'cs':
            command = 'save'
            filename = args[0]
        elif action == 'cl':
            command = 'load'
            filename = args[0]


        filename = os.path.join(config['configdir'], filename + '.json')
        if command == 'save':

            if not os.path.isdir(config['configdir']):
                os.mkdir(config['configdir'])

            with open(filename, 'w') as f:
                f.write(json.dumps(config, indent=4))
        elif command == 'load':
            if os.path.isfile(filename):
                config = json.load(open(filename, 'r'))

    elif action in ['help', 'hp', 'h', '?']:
        
        args_help = json.load(open('src/static/args-help.json', 'r'))
        print(args_help['desc'])
        for item in args_help['actions']:
            item_args = ' | '.join([x for x in item['args']])

            print(
                '   ',
                (item['name'] + ' | ' + item['alias']).ljust(24, ' '),
                item_args.ljust(24, ' '),
                item['desc'],
            )
            print()

        exit()

    return config


if __name__ == "__main__":

    config = parse_args(*sys.argv)

    results = get_results(config)
    show_results(results, config)

    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))