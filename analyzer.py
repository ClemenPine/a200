from typing import Dict
import itertools

JSON = Dict[str, any]


def get_table():
    fingers = ['LP', 'LR', 'LM', 'LI', 'LT', 'RT', 'RI', 'RM', 'RR', 'RP']
    sequences = [item for item in itertools.product(fingers, repeat=3)]
    

    table = {}
    for sequence in sequences:
        trigram_type = ''

        if sequence[0][0] == sequence[2][0]:
            if sequence[0][0] == sequence[1][0]:
                if (
                    (
                        fingers.index(sequence[0]) <
                        fingers.index(sequence[1]) <
                        fingers.index(sequence[2])
                    ) or
                    (
                        fingers.index(sequence[0]) >
                        fingers.index(sequence[1]) >
                        fingers.index(sequence[2])
                    )
                ):
                    trigram_type = "onehand"
                else:
                    trigram_type = "redirect"
            else:
                trigram_type = "alternate"
        else:
            trigram_type = "roll"

        if sequence[0] == sequence[1] or sequence[1] == sequence[2]:
            trigram_type = "sfb"

        table['-'.join(sequence)] = trigram_type
    
    return dict(sorted(table.items(), key=lambda x:x[1], reverse=True))
    


def count_trigrams(keys: JSON, data: JSON):
    table = get_table()

    trigram_data = {
        'roll': 0,
        'alternate': 0,
        'redirect': 0,
        'onehand': 0,
        'sfb': 0,
    }

    for trigram in data['3-grams']:
        fingers = []
        for char in trigram:
            if char == ' ':
                fingers.append("LT")
            else:
                fingers.append(keys['keys'][char.lower()]['finger'])

        key = '-'.join(fingers)
        if key in table:
            trigram_data[table[key]] += data['3-grams'][trigram]

    for stat in trigram_data:
        trigram_data[stat] /= sum(data['3-grams'].values())

    print(trigram_data)


import layout
import json
keys = layout.create("ylrdwjmou,csntgphaeixzqvkbf'/.")
data = json.load(open('data/200-data.json', 'r'))
count_trigrams(keys, data)