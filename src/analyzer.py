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


def get_stats(keys: JSON, data: JSON, thumb: str):

    keys['keys'][' '] = {'finger': thumb}

    table = get_table()
    trigrams = {x: 0 for x in set(table.values()).union({'unknown', 'sfR'})}
    
    for gram, val in data['3-grams'].items():
        
        fingers = []
        for char in gram:

            if thumb == 'NONE' and char == ' ':
                break

            if char in keys['keys']:
                finger = keys['keys'][char]['finger']
                fingers.append(finger)
        else:
            seq = '-'.join(fingers)

            if seq in table:
                if len(set(gram)) < len(gram):
                    key = 'sfR'
                else:
                    key = table[seq]
            else:
                key = 'unknown'
            
            trigrams[key] += val

    total = sum(trigrams.values())
    trigrams = {k: v / total for k, v in trigrams.items()}

    return trigrams


def get_secondary_stats(stats: JSON):
    trigrams = {}

    trigrams['roll'] = stats['roll-in'] + stats['roll-out']
    trigrams['onehand'] = stats['oneh-in'] + stats['oneh-out']
    trigrams['dsfb'] = stats['dsfb-alt'] + stats['dsfb-red']

    if stats['roll-out']:
        trigrams['roll-rt'] = stats['roll-in'] / stats['roll-out']
    else:
        trigrams['roll-rt'] = float('inf')

    if stats['oneh-out']:
        trigrams['oneh-rt'] = stats['oneh-in'] / stats['oneh-out']
    else:
        trigrams['oneh-rt'] = float('inf')

    return trigrams


def count_trigrams(keys: JSON, data: JSON, thumb: str):
    primary = get_stats(keys, data, thumb)
    secondary = get_secondary_stats(primary)

    return primary | secondary


def get_results(keys: JSON, data: JSON, config: JSON):
    
    results = {
        'trigrams': {},
        'finger-use': count_finger_use(keys, data, config['thumb-space']),
        'row-use': count_row_use(keys, data),
    }

    if config['thumb-space'] in ['LT', 'RT', 'NONE']:
        results['trigrams'] = count_trigrams(keys, data, config['thumb-space'])
    elif config['thumb-space'] in ['AVG']:
        left_trigrams = count_trigrams(keys, data, 'LT')
        right_trigrams = count_trigrams(keys, data, 'RT')
        for stat in left_trigrams:
            results['trigrams'][stat] = (left_trigrams[stat] + right_trigrams[stat]) / 2

    return {k: v for d in results for k, v in results[d].items()}