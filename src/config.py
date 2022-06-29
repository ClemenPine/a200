import os
import json
from typing import Dict, List

import layout

JSON = Dict[str, any]

def init():
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


def load(path: str):
    if os.path.isfile(path):

        with open(path, 'r') as f:
            config = json.load(f)
    else:
        config = init()

    return config


def write(config: JSON, *, path: str): 
    with open(path, 'w') as f:
        f.write(json.dumps(config, indent=4))


def get_colors(config: JSON):
    color_path = os.path.join(config['themedir'], config['theme'] + '.json')
    
    with open(color_path, 'r') as f:
        colors = json.load(f)['colors']

    return colors


def set_sort(config: JSON, *, sorts: Dict[str, float], dir: str='HIGH'):
    config['sort'] = sorts
    config['sort-high'] = dir == 'HIGH'


def set_filter(config: JSON, *, filters: Dict[str, float]):
    config['filter'] = filters


def set_mode(config: JSON, *, layouts: List[str]):
    config['single-mode']['active'] = bool(layouts)
    config['single-mode']['layouts'] = [x.lower() for x in layouts]


def set_thumb(config: JSON, *, thumb: str):
    thumb = thumb.upper()
    if thumb in ['LT', 'RT', 'NONE', 'AVG']:
        config['thumb-space'] = thumb


def set_data(config: JSON, *, data: str):
    set_file(config, file=data, key='datafile', dir=config['datadir'])


def set_theme(config: JSON, *, theme: str):
    set_file(config, file=theme, key='theme', dir=config['themedir'])


def set_file(config: JSON, *, file: str, key: str, dir: str):
    path = os.path.join(dir, file + '.json')
    if os.path.isfile(path):
        config[key] = file


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


def toggle_columns(config: JSON, *, columns: List[str]):
    toggle(config, targets=columns, axis='columns')


def toggle_layouts(config: JSON, *, layouts: List[str]):
    toggle(config, targets=layouts, axis='layouts')


def toggle(config: JSON, *, targets: List[str], axis: str):

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
