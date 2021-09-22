import json
import random
import glob
from typing import Dict

def load_file(filename: str):
    
    fingers = ['LP', 'LR', 'LM', 'LI', 'RI', 'RM', 'RR', 'RP']

    shifted = dict(zip(
        "abcdefghijklmnopqrstuvwxyz,./;'-=[]",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ<>?:\"_+{}"
    ))

    keys = {
        'name': "[unknown]",
        'keys': {},
    }

    with open(filename, 'r') as f:
        tokens = [word for word in f.read().split()]

    keys['name'] = tokens.pop(0)

    chars = tokens[:len(tokens) // 2]
    indexes = tokens[len(tokens) // 2:]

    keymap = dict(zip(chars, indexes))
    for item in keymap:
        finger = fingers[int(keymap[item])]
        if len(item) == 2:
            keys['keys'][item[0]] = {
                'finger': finger,
                'shift': False
            }
            keys['keys'][item[1]] = {
                'finger': finger,
                'shift': True
            }
        else:
            keys['keys'][item] = {
                'finger': finger,
                'shift': False
            }
            if item in shifted:
                keys['keys'][shifted[item]] = {
                    'finger': finger,
                    'shift': True
                }

    return keys

def load_dir(dirname: str):
    layouts = []
    for filename in glob.glob(dirname + "/*"):
        layouts.append(load_file(filename))

    return layouts