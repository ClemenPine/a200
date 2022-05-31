import sys
import os
import json
import shutil
import copy
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


def print_color(item: JSON, metric: str, data: JSON, config: JSON, isPercent: bool=True):

    # get percentage of layouts worse
    percent = get_layout_percent(item, metric, data)

    # get string

    if isPercent:
        string = "{:.2%}".format(item['metrics'][metric]).rjust(6, ' ') + '  '
    else:
        string = "{0:.2f}".format(item['metrics'][metric]).rjust(6, ' ') + ' '

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

    if config['filter']:
        print("filter by:", end='   ')
        for filter in config['filter']:
            print(
                filter, 
                "{:.2%}".format(config['filter'][filter]),
                end='   '
            )
        print()

    if config['sort']:
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

    # get filters
    filters = []
    for name, val in config['filter'].items():
        
        filter = {
            'name': name,
            'dir': val // abs(val),
            'cutoff': abs(val)
        }

        filters.append(filter)

    # print rows
    for item in results['data']:

        if item['name'].lower() not in config['layouts']:
            config['layouts'][item['name'].lower()] = True

        # ignore hidden layouts 
        if not config['layouts'][item['name'].lower()]:
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
            print((item['name'] + '\033[38;5;250m' + ' ').ljust(36, '-') + '\033[0m', end=' ')
            for metric, value in flatten(config['columns']).items():
                if value:
                    print_color(item, metric, results, config, metric not in ['roll-rt', 'oneh-rt'])
            print()


def print_layout(results: JSON, config: JSON):

    print(results['file'].upper())
    print(("thumb: " + config['thumb-space']).ljust(22, ' '))

    for item in [item for item in results['data'] if config['layouts'][item['name'].lower()] == True]:
        
        print()

        # header
        print(item['name'])
        layout.pretty_print(item['file'], config)
        print()

        print('Trigrams')
        print('========')

        # alternation
        print('Alternates -'.rjust(12, ' '), end=' ')
        print('Total:', end=' ')
        print_color(item, 'alternate', results, config)
        print()

        # rolls
        print('Rolls -'.rjust(12, ' '), end=' ')
        print('Total:', end=' ')
        print_color(item, 'roll', results, config)
        print('In:', end=' ')
        print_color(item, 'roll-in', results, config),
        print('Out:', end=' ')
        print_color(item, 'roll-out', results, config)
        print('Ratio:', end=' ')
        print_color(item, 'roll-rt', results, config, False)
        print()

        # onehands
        print('Onehands -'.rjust(12, ' '), end=' ')
        print('Total:', end=' ')
        print_color(item, 'onehand', results, config)
        print('In:', end=' ')
        print_color(item, 'oneh-in', results, config),
        print('Out:', end=' ')
        print_color(item, 'oneh-out', results, config)
        print('Ratio:', end=' ')
        print_color(item, 'oneh-rt', results, config, False)
        print()

        # redirects
        print('Redirects -'.rjust(12, ' '), end=' ')
        print('Total:', end=' ')
        print_color(item, 'redirect', results, config)
        print()

        # unknown
        if item['metrics']['unknown'] > 0:
            print('Unknown -'.rjust(12, ' '), end=' ')
            print('Total:', end=' ')
            print_color(item, 'unknown', results, config)
            print()

        print()

        # sfb/dsfb/sfT/sfR
        print('Same Finger')
        print('===========')

        print('SFB -'.rjust(12, ' '), end='')
        print_color(item, 'sfb', results, config)
        print('DSFB -'.rjust(12, ' '), end='')
        print_color(item, 'dsfb', results, config)
        print()

        print('SFT -'.rjust(12, ' '), end='')
        print_color(item, 'sfT', results, config)
        print('SFR -'.rjust(12, ' '), end='')
        print_color(item, 'sfR', results, config)
        print()

        print()

        # finger use
        print("Finger Use")
        print("==========")

        print('Left -'.rjust(12, ' '), end=' ')
        print('Total:', end=' ')
        print_color(item, 'LTotal', results, config)
        for finger in ['LP','LR','LM','LI']:
            print(finger + ':', end=' ')
            print_color(item, finger, results, config)
        print()

        print('Right -'.rjust(12, ' '), end=' ')
        print('Total:', end=' ')
        print_color(item, 'RTotal', results, config)
        for finger in ['RP','RR','RM','RI']:
            print(finger + ':', end=' ')
            print_color(item, finger, results, config)
        print()

        if (config['thumb-space'] != 'NONE'):
            print('Thumb -'.rjust(12, ' '), end=' ')
            print('Total:', end=' ')
            print_color(item, 'TB', results, config)
            print()

        print()

        # row use
        print("Row Use")
        print("=======")

        print('Top -'.rjust(12, ' '), end=' ')
        print_color(item, 'top', results, config)
        print('Home -'.rjust(12, ' '), end=' ')
        print_color(item, 'home', results, config)
        print('Bottom -'.rjust(12, ' '), end=' ')
        print_color(item, 'bottom', results, config)
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
    if action in ['view', 'vw']:
        config['single-mode']['active'] = len(args) != 0
        config['single-mode']['layouts'] = [x.lower() for x in args]

    elif action in ['toggle', 'tg', 'tc', 'tl']:

        config['single-mode']['active'] = False

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

        config['single-mode']['active'] = False

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
                    if arg[0] == '-':
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

    elif action in ['filter', 'fl']:

        config['single-mode']['active'] = False

        config['filter'] = {}

        # parse metric string
        for arg in args:
            arg = arg.split('%')

            config['filter'][arg[1]] = arg[0]
        
        # convert to float
        for item in config['filter']:
            config['filter'][item] = float(config['filter'][item]) / 100

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

    elif action in ['cache', 'cc']:

        shutil.rmtree(config['cachedir'])

    elif action in ['help', 'hp', 'h', '?']:
        
        config['single-mode']['active'] = False

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

    elif action == None:

        config['single-mode']['active'] = False

    return config


if __name__ == "__main__":

    config = parse_args(*sys.argv)

    if config['single-mode']['active']:
        layout_config = copy.deepcopy(config)
        layout_config['layouts'] = {item: False for item in layout_config['layouts']}

        for layout_name in layout_config['single-mode']['layouts']:
            layout_config['layouts'][layout_name] = True
    
        results = get_results(layout_config)
        print_layout(results, layout_config)
    else:
        results = get_results(config)
        show_results(results, config)

    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))