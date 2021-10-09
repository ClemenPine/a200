from typing import List
import json

def get_monograms(file: str):

    texts = json.load(open(file, 'r'))['texts']

    monograms = {' ': 0}
    for word in texts:
        for char in word:
            if not char in monograms:
                monograms[char] = 1
            else:
                monograms[char] += 1
        monograms[' '] += 1

    return dict(sorted(monograms.items(), key=lambda x: x[1], reverse=True))
   


def get_trigrams(file: str):
    
    texts = json.load(open(file, 'r'))['texts']
    
    trigrams = {}

    counts = {
        'start': {},
        'end': {},
    }

    word_count = len(texts)
    for word in texts:

        padded_word = ' ' + word + ' '
        for i in range(len(padded_word) - 2):
            seq = padded_word[i:i+3]
            if not seq in trigrams:
                trigrams[seq] = word_count
            else:
                trigrams[seq] += word_count

        if not word[0] in counts['start']:
            counts['start'][word[0]] = 1
        else:
            counts['start'][word[0]] += 1

        if not word[-1] in counts['end']:
            counts['end'][word[-1]] = 1
        else:
            counts['end'][word[-1]] += 1

    for start in counts['start']:
        for end in counts['end']:
            trigrams[end + ' ' + start] = counts['start'][start] * counts['end'][end]

    return dict(sorted(trigrams.items(), key=lambda x: x[1], reverse=True))


if __name__ == '__main__':

    file = 'monkeytype-450k'

    results = {
        'file': 'wordlists/' + file + '.json',
        '1-grams': {},
        '3-grams': {},
    }

    results['1-grams'] = get_monograms(results['file'])
    results['3-grams'] = get_trigrams(results['file'])

    with open(file + '.json', 'w') as f:
        f.write(json.dumps(results, indent=4))