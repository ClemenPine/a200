import sys
import os
import json
import shutil
import copy
import layout, analyzer
from typing import Dict, List

JSON = Dict[str, any]


def init_config():

    default_path = os.path.join('src', 'static', 'config-init.json')
    init_path = 'init-config.json'

    # use init-config if present
    if os.path.isfile(init_path):
        path = init_path
    else:
        path = default_path

    with open(path, 'r') as f:
        config = json.load(f)
    layouts = layout.load_dir(config['layoutdir'])  

    # enable layouts by default
    for keys in layouts:
        name = keys['name'].lower()
        config['layouts'][name] = True  

    return config


def get_layout_percent(item: JSON, metric: str, results: JSON):

    wins = 0
    item_metric = item['metrics'][metric]

    for result in results['data']:
        result_metric = result['metrics'][metric]

        if item_metric > result_metric:
            wins += 1
        
    percent = wins / len(results['data'])
    return percent


def color(item: JSON, metric: str, data: JSON, config: JSON, isPercent: bool=True):

    # get percentage of layouts worse
    percent = get_layout_percent(item, metric, data)

    # get string
    value = item['metrics'][metric]
    if isPercent:
        string = f'{value:>6.2%}  '
    else:
        string = f'{value:>6.2f}  '    

    # get theme
    color_path = os.path.join(config['themedir'], config['theme'] + '.json')
    with open(color_path, 'r') as f:
        colors = json.load(f)['colors'] 

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


def get_results(config: JSON):

    cache_path = os.path.join(config['cachedir'], 'cached-' + config['datafile'] + '.json')
    data_path = os.path.join(config['datadir'], config['datafile'] + '.json')

    # create cache dir if one isn't available
    if not os.path.isdir(config['cachedir']):
        os.mkdir(config['cachedir'])

    # create cache or load empty one
    if os.path.isfile(cache_path):

        with open(cache_path, 'r') as f:
            cache = json.load(f)
    else:   
        cache = {
            'file': config['datafile'],
            'data': {}
        }

    # load data
    with open(data_path, 'r') as f:
        data = json.load(f)

    results = {
        'file': data['file'],
        'data': []
    }

    layouts = layout.load_dir(config['layoutdir'])
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
    with open(cache_path, 'w') as f:
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
        print('filter by:  ', end='')

        for filter, val in config['filter'].items():
            print(f'{filter} {val:.2%}  ', end='')
        print()

    if config['sort']:
        print('sort by:  ', end='')

        for sort, val in config['sort'].items():
            print(f'{sort} {val:.0%}  ', end='')
        print()

    print(f'thumb: {config["thumb-space"]:<16}', end='')

    # print column names
    for metric, value in flatten(config['columns']).items():
        if value:
            print(f'{metric:>8} ',end='')
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
        layout_name = item['name'].lower()

        # enable new layouts by default
        if layout_name not in config['layouts']:
            config['layouts'][layout_name] = True

        # ignore hidden layouts 
        if not config['layouts'][layout_name]:
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
            for metric, value in flatten(config['columns']).items():
                if value:
                    print(color(item, metric, results, config, metric not in ['roll-rt', 'oneh-rt']), end=' ')
            print()


def print_layout(results: JSON, config: JSON):

    print(results['file'].upper())
    print(f'thumb: {config["thumb-space"]}')

    layouts = [item for item in results['data'] if config['layouts'][item['name'].lower()] == True]
    for item in layouts:

        # calculate colors
        cl = {}
        for metric in item['metrics']:
            cl[metric] = color(item, metric, results, config)

        print()

        # header
        print(item['name'])
        layout.pretty_print(item['file'], config)
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

        if (config['thumb-space'] != 'NONE'):
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