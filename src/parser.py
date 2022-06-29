import json
import math
import shutil
import itertools
from typing import Dict

import config

def parse_args(name='', action=None, *args):
    column_toggles = [' '.join(x) for x in itertools.product(['tg', 'toggle'], ['c', 'cs', 'column', 'columns'])]
    layout_toggles = [' '.join(x) for x in itertools.product(['tg', 'toggle'], ['l', 'ls', 'layout', 'layouts'])]

    # open/init conf
    conf = config.load('config.json')

    # parse args
    if action in ['view', 'vw']:
        config.set_mode(conf, layouts=args)

    elif action in ['tc']:
        config.toggle_columns(conf, columns=args)

    elif args and ' '.join([action, args[0]]) in column_toggles:
        config.toggle_columns(conf, columns=args[1:])

    elif action in ['tl']:
        config.toggle_layouts(conf, layouts=args)

    elif args and ' '.join([action, args[0]]) in layout_toggles:
        config.toggle_layouts(conf, layouts=args[1:])

    elif action in ['sort', 'st']:
        total = 0
        count = 0

        sorts = {}
        for arg in args:
            arg = arg.split('%')

            if len(arg) > 1:
                val = float(arg[0]) / 100
                sorts[arg[1]] = val
                total += abs(val)
            elif arg[0][0] == '-':
                sorts[arg[0].split('-')[-1]] = -0.0
                count += 1
            else:
                sorts[arg[0].split('-')[-1]] = 0.0
                count += 1

        if count:
            percent_left = (1 - total) / count
        else:
            percent_left = 0

        for metric, val in sorts.items():
            if val == 0:
                sorts[metric] = math.copysign(percent_left, val)

        config.set_sort(conf, sorts=sorts)
        config.set_mode(conf, layouts=[])

    elif action in ['filter', 'fl']:
        filters = {}
        for arg in args:
            arg = arg.split('%')

            filters[arg[1]] = float(arg[0]) / 100
            
        config.set_filter(conf, filters=filters)
        config.set_mode(conf, layouts=[])

    elif action in ['thumb', 'tb']:     
        config.set_thumb(conf, thumb=args[0])

    elif action in ['data', 'dt']:
        config.set_data(conf, data=args[0])

    elif action in ['theme', 'tm']:
        config.set_theme(conf, theme=args[0])
        
    elif action in ['reset']:
        conf = config.init()

    elif action in ['cs']:
        config.write(conf, path=f'{args[0]}.json')

    elif args and ' '.join([action, args[0]]) in ['config save']:
        config.write(conf, path=f'{args[1]}.json')

    elif action in ['cl']:
        conf = config.load(f'{args[0]}.json')

    elif args and ' '.join([action, args[0]]) in ['config load']:
        conf = config.load(f'{args[1]}.json')

    elif action in ['cache', 'cc']:
        shutil.rmtree(conf['cachedir'])

    elif action in ['help', 'hp', 'h', '?']:
        args_help = json.load(open('src/static/args-help.json', 'r'))

        print(args_help['desc'])
        for item in args_help['actions']:
            item_actions = ' || '.join([item['name'], item['alias']])
            item_args = ' | '.join([x for x in item['args']])

            print(f'\n  {item_actions:<24} {item_args:<24} {item["desc"]}')

        config.set_mode(conf, layouts=[])
        exit()

    elif action == None:
        config.set_mode(conf, layouts=[])

    return conf