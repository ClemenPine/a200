import json
import random
from typing import Dict


primary_map = [
    'LP','LR','LM','LI','LI','RI','RI','RM','RR','RP',
    'LP','LR','LM','LI','LI','RI','RI','RM','RR','RP',
    'LP','LR','LM','LI','LI','RI','RI','RM','RR','RP'
]

alt_map = [
    ### TODO ###
]

row_map = ['top', 'middle', 'bottom']


def create(key_string: str, name: str = "[unknown]"):
    
    # arg checks
    if len(key_string) != 30:
        raise ValueError("key string must be exactly 30 characters")
    

    keys = {
        'name': name,
        'keys': {letter: {} for letter in key_string}
    }

    for i, letter in enumerate(keys['keys']):
        keys['keys'][letter] = {
            'finger': primary_map[i % 10],
            'row': row_map[i // 10]
        }

    return keys


def create_random():
    letters = list("abcdefghijklmnopqrstuvwxyz,.'/")
    random.shuffle(letters)

    
    return create(''.join(letters), "random")


def load(filename: str = 'layouts.json'):
    # load from file and create each one
    layouts = json.load(open(filename, 'r'))['layouts']
    for name in layouts:
        keys = create(layouts[name], name)
        layouts[name] = keys
    return layouts


def save(keys: Dict[str, any], filename: str = 'outfile.json'):
    # writes to file exactly as stored in the program, in json format
    with open(filename, 'w') as f:
        f.write(json.dumps(keys))