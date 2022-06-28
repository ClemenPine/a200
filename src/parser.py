import os
import json
import shutil
from typing import Dict

import config

JSON = Dict[str, any]

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

    # open/init conf
    conf = config.load()

    # parse args
    if action in ['view', 'vw']:
        config.set_mode(conf, layouts=args)

    elif action in ['toggle', 'tg', 'tc', 'tl']:

        conf['single-mode']['active'] = False

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
                set_states(conf[axis], not True in get_states(conf[axis]))
            else:
                section = find_section(conf[axis], target)[0]
                if type(section[target]) == bool:
                    section[target] = not section[target]
                else:
                    set_states(section[target], not True in get_states(section[target]))

    elif action in ['sort', 'st']:

        count = 0
        total_percent = 0

        sort_infos = []
        for arg in args:

            arg = arg.split('%')
            sort = {
                'dir': 'LOW' if arg[0][0] == '-' else 'HIGH',
                'metric': arg[-1].split('-')[-1],
                'value': float(arg[0].split('-')[-1]) / 100 if len(arg) > 1 else 0
            }

            if sort['value']:
                total_percent += sort['value']
            else:
                count += 1

            sort_infos.append(sort)

        if count:
            percent_left = (1 - total_percent) / count
        else:
            percent_left = 0

        sorts = {}
        for sort in sort_infos:

            if sort['value'] == 0:
                sort['value'] = percent_left

            metric = sort['metric']
            if sort['dir'] == 'HIGH':
                value = sort['value']
            else:
                value = -sort['value']

            sorts[metric] = value
        
        config.set_sort(conf, sorts=sorts)
        config.set_mode(conf, layouts=[])

    elif action in ['filter', 'fl']:

        conf['single-mode']['active'] = False

        conf['filter'] = {}

        # parse metric string
        for arg in args:
            arg = arg.split('%')

            conf['filter'][arg[1]] = arg[0]
        
        # convert to float
        for item in conf['filter']:
            conf['filter'][item] = float(conf['filter'][item]) / 100

    elif action in ['thumb', 'tb']:     
        config.set_thumb(conf, thumb=args[0])

    elif action in ['data', 'dt']:
        config.set_data(conf, data=args[0])

    elif action in ['theme', 'tm']:
        config.set_theme(conf, theme=args[0])
        
    elif action in ['reset']:
        conf = config.init()

    elif action in ['conf', 'cs', 'cl']:

        if action in ['conf', 'cg']:
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


        filename = os.path.join(conf['confdir'], filename + '.json')
        if command == 'save':

            if not os.path.isdir(conf['confdir']):
                os.mkdir(conf['confdir'])

            with open(filename, 'w') as f:
                f.write(json.dumps(conf, indent=4))
        elif command == 'load':
            if os.path.isfile(filename):
                conf = json.load(open(filename, 'r'))

    elif action in ['cache', 'cc']:
        shutil.rmtree(conf['cachedir'])

    elif action in ['help', 'hp', 'h', '?']:
        
        config.set_mode(conf, layouts=[])

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
        config.set_mode(conf, layouts=[])

    return conf