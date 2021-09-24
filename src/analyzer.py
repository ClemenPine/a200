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

    for stat in trigram_data:
        trigram_data[stat] /= sum(data['3-grams'].values())

    return trigram_data