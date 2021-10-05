from typing import Dict
import itertools

JSON = Dict[str, any]


def get_table():

    fingers = {
        'LP': 0,
        'LR': 1,
        'LM': 2,
        'LI': 3,
        'LT': 4,
        'RT': 5,
        'RI': 6,
        'RM': 7,
        'RR': 8,
        'RP': 9,
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
            seq[0][0] != seq[2][0]
        ):
            trigram_type = 'roll'

        elif (
            (
                fingers[seq[0]] < 
                fingers[seq[1]] <
                fingers[seq[2]]
            ) or
            (
                fingers[seq[0]] >
                fingers[seq[1]] >
                fingers[seq[2]]
            )
        ):
            trigram_type = 'onehand'

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
            seq[0] != seq[1]
        ):
            trigram_type = 'dsfb'
        
        elif (
            seq[0] == seq[1] and
            seq[1] == seq[2]
        ):
            trigram_type = 'sfT'
        
        table['-'.join(seq)] = trigram_type
    
    return dict(sorted(table.items(), key=lambda x:x[1], reverse=True))
    

def count_finger_use(keys: JSON, data: JSON):

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
            counts[keys['keys'][char]['finger']] += data['1-grams'][char]

    total = sum(counts.values())
    for finger in counts:
        counts[finger] /= total

    return counts  


def count_trigrams(keys: JSON, data: JSON, thumb: str):

    table = get_table()

    trigram_data = {
        'roll': 0,
        'alternate': 0,
        'redirect': 0,
        'onehand': 0,
        'sfb': 0,
        'dsfb': 0,
        'sfT': 0,
        'sfR': 0,
    }

    for trigram in data['3-grams']:
        
        fingers = []
        for char in trigram:
            if char == ' ':
                fingers.append(thumb)
            else:
                fingers.append(keys['keys'][char]['finger'])
        
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

    total = sum(trigram_data.values())
    for stat in trigram_data:
        trigram_data[stat] /= total

    return trigram_data


def get_results(keys: JSON, data: JSON, config: JSON):
    
    results = {
        'trigrams': {},
        'finger-use': count_finger_use(keys, data),
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