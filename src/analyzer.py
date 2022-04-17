from typing import Dict
import itertools

JSON = Dict[str, any]


def get_table():

    fingers = {
        'LP': 4,
        'LR': 3,
        'LM': 2,
        'LI': 1,
        'LT': 0,
        'RT': 0,
        'RI': 1,
        'RM': 2,
        'RR': 3,
        'RP': 4,
    }
    sequences = [item for item in itertools.product(fingers.keys(), repeat=3)]
    
    table = {}
    for seq in sequences:
        
        # trigrams
        if (
            seq[0][0] == seq[2][0] and
            seq[0][0] != seq[1][0]
        ):
            trigram_type = 'alternate'

        elif (
            (
                seq[0][0] != seq[2][0] and
                seq[0][0] == seq[1][0] and
                fingers[seq[0]] < fingers[seq[1]]
            ) or
            (
                seq[0][0] != seq[2][0] and
                seq[1][0] == seq[2][0] and
                fingers[seq[1]] < fingers[seq[2]]
            )
        ):
            trigram_type = 'roll-out'

        elif (
            (
                seq[0][0] != seq[2][0] and
                seq[0][0] == seq[1][0] and
                fingers[seq[0]] > fingers[seq[1]]
            ) or
            (
                seq[0][0] != seq[2][0] and
                seq[1][0] == seq[2][0] and
                fingers[seq[1]] > fingers[seq[2]]
            )
        ):
            trigram_type = 'roll-in'

        elif (
            fingers[seq[0]] >
            fingers[seq[1]] >
            fingers[seq[2]]
        ):
            trigram_type = 'oneh-in'

        elif (
            
            fingers[seq[0]] < 
            fingers[seq[1]] <
            fingers[seq[2]]
        ):
            trigram_type = 'oneh-out'

        else:
            trigram_type = 'redirect'

        # sfs 
        if (
            seq[0] != seq[2] and
            seq[1] in [seq[0], seq[2]]
        ):
            trigram_type = 'sfb'

        elif (
            seq[0] == seq[2] and
            seq[0] != seq[1] and
            seq[0][0] == seq[1][0]
        ):
            trigram_type = 'dsfb-red'

        elif (
            seq[0] == seq[2] and
            seq[0] != seq[1] and
            seq[0][0] != seq[1][0]
        ):
            trigram_type = 'dsfb-alt'
        
        elif (
            seq[0] == seq[1] and
            seq[1] == seq[2]
        ):
            trigram_type = 'sfT'
        
        table['-'.join(seq)] = trigram_type
    
    return dict(sorted(table.items(), key=lambda x:x[1], reverse=True))
    

def count_finger_use(keys: JSON, data: JSON, thumb: str):

    counts = {
        'LP': 0,
        'LR': 0,
        'LM': 0,
        'LI': 0,
        'RI': 0,
        'RM': 0,
        'RR': 0,
        'RP': 0,
        'TB': 0,
    }

    for char in data['1-grams']:
        if char == ' ':
            counts['TB'] = data['1-grams'][char]
        else:
            if not char in keys['keys']:
                pass
            else:
                counts[keys['keys'][char]['finger']] += data['1-grams'][char]

    if thumb == 'NONE':
        counts['TB'] = 0

    total = sum(counts.values())
    for finger in counts:
        counts[finger] /= total

    counts['LTotal'] = sum({x: counts[x] for x in counts if x in ['LP', 'LR', 'LM', 'LI']}.values())
    counts['RTotal'] = sum({x: counts[x] for x in counts if x in ['RP', 'RR', 'RM', 'RI']}.values())

    return counts  


def count_row_use(keys: JSON, data: JSON):
    
    counts = {
        'top': 0,
        'home': 0,
        'bottom': 0,
    }

    for char in data['1-grams']:
        if char in keys['keys'] and 'row' in keys['keys'][char]:
            row = ['top', 'home', 'bottom'][keys['keys'][char]['row']]
            counts[row] += data['1-grams'][char]
    
    total = sum(counts.values())
    for finger in counts:
        counts[finger] /= total

    return counts


def count_trigrams(keys: JSON, data: JSON, thumb: str):

    table = get_table()

    trigram_data = {
        'roll-in': 0,
        'roll-out': 0,
        'alternate': 0,
        'redirect': 0,
        'oneh-in': 0,
        'oneh-out': 0,
        'sfb': 0,
        'dsfb-alt': 0,
        'dsfb-red': 0,
        'sfT': 0,
        'sfR': 0,
        'unknown': 0,
    }

    for trigram in data['3-grams']:
        
        fingers = []
        for char in trigram:
            if char == ' ':
                if thumb == 'NONE':
                    break
                else:
                    fingers.append(thumb)
            else:
                if not char in keys['keys']:
                    pass
                else:
                    fingers.append(keys['keys'][char]['finger'])
        else:
            key = '-'.join(fingers)
            if key in table:
                if (
                    trigram[0] == trigram[1] or
                    trigram[1] == trigram[2] or
                    trigram[0] == trigram[2]
                ):
                    trigram_data['sfR'] += data['3-grams'][trigram]
                else:
                    trigram_data[table[key]] += data['3-grams'][trigram]
            else:
                trigram_data['unknown'] += data['3-grams'][trigram]

    total = sum(trigram_data.values())
    for stat in trigram_data:
        trigram_data[stat] /= total

    trigram_data['roll'] = trigram_data['roll-in'] + trigram_data['roll-out']
    trigram_data['onehand'] = trigram_data['oneh-in'] + trigram_data['oneh-out']
    trigram_data['dsfb'] = trigram_data['dsfb-alt'] + trigram_data['dsfb-red']

    if trigram_data['roll-out']:
        trigram_data['roll-rt'] = trigram_data['roll-in'] / trigram_data['roll-out']
    else:
        trigram_data['roll-rt'] = float('inf')

    if trigram_data['oneh-out']:
        trigram_data['oneh-rt'] = trigram_data['oneh-in'] / trigram_data['oneh-out']
    else:
        trigram_data['oneh-rt'] = float('inf')

    return trigram_data


def get_results(keys: JSON, data: JSON, config: JSON):
    
    results = {
        'trigrams': {},
        'finger-use': count_finger_use(keys, data, config['thumb-space']),
        'row-use': count_row_use(keys, data),
    }

    if config['thumb-space'] == 'LT':
        results['trigrams'] = count_trigrams(keys, data, 'LT')
    elif config['thumb-space'] == 'RT':
        results['trigrams'] = count_trigrams(keys, data, 'RT')
    elif config['thumb-space'] == 'NONE':
        results['trigrams'] = count_trigrams(keys, data, 'NONE')
    elif config['thumb-space'] == 'AVG':
        left_trigrams = count_trigrams(keys, data, 'LT')
        right_trigrams = count_trigrams(keys, data, 'RT')
        for stat in left_trigrams:
            results['trigrams'][stat] = (left_trigrams[stat] + right_trigrams[stat]) / 2

    return {k: v for d in results for k, v in results[d].items()}

if __name__ == '__main__':

    import json
    with open('table.json', 'w') as f:
        f.write(json.dumps(get_table(), indent=4))