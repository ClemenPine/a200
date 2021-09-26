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
        if sequence[0] == sequence[2]:
            if sequence[0] == sequence[1]:
                trigram_type = 'sfT'
            else:
                trigram_type = 'dsfb'

        table['-'.join(sequence)] = trigram_type
    
    return dict(sorted(table.items(), key=lambda x:x[1], reverse=True))
    

def count_finger_use(keys: JSON, data: JSON, config: JSON):

    counts = {
        'LP': 0,
        'LR': 0,
        'LM': 0,
        'LI': 0,
        'RI': 0,
        'RM': 0,
        'RR': 0,
        'RP': 0,
        config['thumb-space']: 0,
    }

    for char in data['1-grams']:
        if char == ' ':
            counts[config['thumb-space']] = data['1-grams'][char]
        else:
            counts[keys['keys'][char]['finger']] += data['1-grams'][char]

    for finger in counts:
        counts[finger] /= sum(data['1-grams'].values())

    return counts  


def count_trigrams(keys: JSON, data: JSON, config: JSON):

    table = get_table()

    trigram_data = {
        'LT': {
            'roll': 0,
            'alternate': 0,
            'redirect': 0,
            'onehand': 0,
            'sfb': 0,
            'dsfb': 0,
            'sfT': 0,
            'sfR': 0,
        },
        'RT': {
            'roll': 0,
            'alternate': 0,
            'redirect': 0,
            'onehand': 0,
            'sfb': 0,
            'dsfb': 0,
            'sfT': 0,
            'sfR': 0,
        }
    }

    if config['thumb-space'] == 'LT':
        trigram_data.pop('RT')
    elif config['thumb-space'] == 'RT':
        trigram_data.pop('LT')
    elif config['thumb-space'] == 'NONE':
        trigram_data.pop('RT')

    for trigram in data['3-grams']:

        if config['thumb-space'] == 'NONE' and ' ' in trigram:
            continue

        fingers = []
        for thumb in trigram_data:
            key = []
            for char in trigram:
                if char == ' ':
                    key.append(thumb)
                else:
                    key.append(keys['keys'][char]['finger'])
            fingers.append(key)

            key = '-'.join(key)

            if key in table:
                if (
                    trigram[0] == trigram[1] or
                    trigram[1] == trigram[2] or
                    trigram[0] == trigram[2]
                ):
                    trigram_data[thumb]['sfR'] += data['3-grams'][trigram]
                else:
                    trigram_data[thumb][table[key]] += data['3-grams'][trigram]


    for thumb in trigram_data:
        for stat in trigram_data[thumb]:
            trigram_data[thumb][stat] /= sum(data['3-grams'].values())
        
    if config['thumb-space'] == 'LT':
        return trigram_data['LT']
    elif config['thumb-space'] == 'RT':
        return trigram_data['RT']
    elif config['thumb-space'] == 'AVG':
        data = {}
        for stat in trigram_data['LT']:
            data[stat] = (trigram_data['LT'][stat] + trigram_data['RT'][stat]) / 2
        return data
    else:
        return trigram_data['LT']