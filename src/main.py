import sys
import os
import json
import layout, analyzer
from typing import Dict, List

JSON = Dict[str, any]


def init_config():
    
    config = json.load(open('src/static/config-init.json', 'r'))
    layouts = layout.load_dir(config['layoutdir'])

    for keys in layouts:
        config['layouts'][keys['name'].lower()] = True

    return config


def print_color(item: JSON, section: str, column_name: str, data: JSON):

    # get percentage of layouts worse
    percent = 0
    for result in data['data']:
        if item[section][column_name] > result[section][column_name]:
            percent += 1
    percent /= len(data['data'])

    # get string
    string = "{:.2%}".format(item[section][column_name]).rjust(6, ' ') + '  '

    # color printing based on percentage
    colors = json.load(open(config['themedir'] + "/" + config['theme'] + ".json"))['colors']
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

    layouts = layout.load_dir(config['layoutdir'])
    data = json.load(open(config['datadir'] + '/' + config['datafile'], 'r'))

    results = {
        'file': data['file'],
        'data': [],
    }

    for keys in layouts:
        trigram_counts = analyzer.count_trigrams(keys, data, config['thumb-space'])
        finger_use = analyzer.count_finger_use(keys, data, config['thumb-space'])
        results['data'].append(
            {
                'name': keys['name'],
                'trigrams': trigram_counts,
                'finger-use': finger_use,
            }
        )

    sort_results(results, config)
    return results


def sort_results(results: List[dict], config: JSON):

    section = [item for item in config['columns'] if config['sort'] in config['columns'][item]]

    if config['sort'] == 'name':
        results['data'] = sorted(results['data'], key=lambda x : x['name'].lower(), reverse=config['sort-high'])
    elif section:
        results['data'] = sorted(results['data'], key=lambda x : x[section[0]][config['sort']], reverse=config['sort-high'])


def show_results(results: List[dict], config: JSON):

    # print metadata
    print(results['file'].upper())
    print("thumb:", config['thumb-space'])
    print(("sort by " + config['sort'].upper() + ":").ljust(22, ' '), end=' ')

    # print column names
    for section in config['columns']:
        for column_name in config['columns'][section]:
            if config['columns'][section][column_name]:
                print(column_name.rjust(8, ' '), end=' ')
    print()

    # print rows
    for item in results['data']:

        # ignore hidden layouts 
        if not config['layouts'][item['name'].lower()]:
            continue

        # print layout stats
        print((item['name'] + '\033[38;5;250m' + ' ').ljust(36, '-') + '\033[0m', end=' ')
        for section in config['columns']:
            for column_name in config['columns'][section]:
                if config['columns'][section][column_name]:
                    print_color(item, section, column_name, results)
        print()
        

def get_states(section: JSON):

    if type(section) == bool:
        return [section]

    states = []
    for item in section:
        states += get_states(section[item])

    return states


def find_section(section: JSON, target: str):
    
    if type(section) == bool:
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
            if target in ['all', 'a']:
                set_states(config[axis], not True in get_states(config[axis]))
            else:
                section = find_section(config[axis], target)[0]
                if type(section[target]) == bool:
                    section[target] = not section[target]
                else:
                    set_states(section[target], not True in get_states(section[target]))

    elif action in ['sort', 'st']:

        if find_section(config['columns'], args[0]):
            config['sort'] = args[0]

        if any(item in args for item in ['high', 'h']):
            config['sort-high'] = True
        elif any(item in args for item in ['low', 'l']):
            config['sort-high'] = False

    elif action in ['thumb', 'tb']:
        
        if args[0].upper() in ['LT', 'RT', 'NONE']:
            config['thumb-space'] = args[0].upper()

    elif action in ['data', 'dt']:
        
        if os.path.isfile(config['datadir'] + '/' + args[0]):
            config['datafile'] = args[0]

    elif action in ['theme', 'tm']:

        if os.path.isfile(config['themedir'] + '/' + args[0] + '.json'):
            config['theme'] = args[0]

    elif action in ['reset']:
        
        config = init_config()

    elif action in ['help', 'hp', 'h', '?']:
        
        # TODO
        print("This is a help page")
        exit()

    return config


if __name__ == "__main__":

    config = parse_args(*sys.argv)

    results = get_results(config)
    show_results(results, config)

    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))