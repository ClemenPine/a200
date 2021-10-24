import json
import hashlib
import glob
import os
from typing import Dict

JSON = Dict[str, any]


def load_file(filename: str):
    
    fingers = ['LP', 'LR', 'LM', 'LI', 'RI', 'RM', 'RR', 'RP', 'LT', 'RT']

    shifted = dict(zip(
        "abcdefghijklmnopqrstuvwxyz,./;'-=[]",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ<>?:\"_+{}"
    ))

    keys = json.load(open('src/static/TEMPLATE.json', 'r'))
    keys['file'] = filename

    with open(filename, 'r') as f:
        tokens = []
        for i, line in enumerate(f.readlines()):
            if i == 0:
                keys['name'] = ' '.join(line.split())
            else:
                tokens.append(line.split())

    hashstr = '-'.join([val for sublist in tokens for val in sublist])
    keys['hash'] = hashlib.md5(hashstr.encode()).hexdigest()

    chars = tokens[:len(tokens) // 2]
    indexes = tokens[len(tokens) // 2:]

    rows = []

    for i in range(len(tokens) // 2):
        rows.append(list(zip(chars[i], indexes[i])))

    for i, keymap in enumerate(rows):
        for j, item in enumerate(keymap):
            finger = fingers[int(item[1])]

            primary = ''
            shift = ''

            if len(item[0]) == 2:
                primary = item[0][0]
                shift = item[0][1]
            else:
                primary = item[0]
                if item[0] in shifted:
                    shift = shifted[item[0]]
                else:
                    shift = None

            keys['keys'][primary] = {
                'finger': finger,
                'row': i,
                'col': j,
                'shift': False,
            }

            if shift:
                keys['keys'][shift] = {
                    'finger': finger,
                    'row': i,
                    'col': j,
                    'shift': True,
                }   

    return keys


def load_dir(dirname: str):
    layouts = []
    for filename in glob.glob(dirname + "/*"):
        layouts.append(load_file(filename))

    return layouts


def pretty_print(filename: str, config: JSON):

    shifted = dict(zip(
        "abcdefghijklmnopqrstuvwxyz,./;'-=[]",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ<>?:\"_+{}"
    ))

    # get tokens
    keys = {}
    with open(filename, 'r') as f:
        tokens = []
        for i, line in enumerate(f.readlines()):
            if i == 0:
                keys['name'] = ' '.join(line.split())
            else:
                tokens.append(line.split())
    
    # theme
    themepath = os.path.join(config['themedir'], config['theme'] + '.json')
    colors = json.load(open(themepath, 'r'))['colors']

    # 1 gram data
    datapath = os.path.join(config['datadir'], config['datafile'] + '.json')
    data = json.load(open(datapath, 'r'))['1-grams']

    data[' '] = 0
    data_total = sum(data.values())

    # print characters
    chars = tokens[:len(tokens) // 2]
    for row in chars:
        for i, key in enumerate(row):
            percent = 0
            if key in data:
                percent += data[key]
            if key in shifted and shifted[key] in data:
                percent += data[shifted[key]]
            percent /= data_total

            if percent > .05:
                print('\033[38;5;' + colors['highest'] + 'm' + key[0] + '\033[0m', end=' ')
            elif percent > .02:
                print('\033[38;5;' + colors['high'] + 'm' + key[0] + '\033[0m', end=' ')
            else:
                print('\033[38;5;' + colors['base'] + 'm' + key[0] + '\033[0m', end=' ')

            if i == len(row) // 2 - 1:
                print('', end=' ')
        print()
    