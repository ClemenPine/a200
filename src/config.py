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


def load():
    path = 'config.json'
    if os.path.isfile(path):

        with open(path, 'r') as f:
            config = json.load(f)
    else:
        config = init()

    return config


def write(config: JSON): 
    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))


def get_colors(config: JSON):
    color_path = os.path.join(config['themedir'], config['theme'] + '.json')
    
    with open(color_path, 'r') as f:
        colors = json.load(f)['colors']

    return colors


def set_sort(config: JSON, *, sorts: Dict[str, float], dir: str='HIGH'):
    config['sort'] = sorts
    config['sort-high'] = dir == 'HIGH'


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


def toggle_columns(config: JSON, *, metrics: List[str]):
    pass
