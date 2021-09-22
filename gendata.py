from typing import List
import json


def get_texts(filename: str):
    return json.load(open(filename, 'r'))['texts']


def get_bigrams(filename: str):
    bigrams = {}
    texts = get_texts(filename)
    for text in texts:
        for i in range(len(text) - 1):
            pair = text[i:i+2]
            if not pair in bigrams:
                bigrams[pair] = 1
            else:
                bigrams[pair] += 1
    
    return dict(sorted(bigrams.items(), key=lambda x:x[1], reverse=True))


def get_ngrams(filename: str, n: int):

    ngrams = {}
    texts = get_texts(filename)

    for j, text in enumerate(texts):

        padded_words = pad_word(text, texts, n - 1)
        for word in padded_words:

            for i in range(len(text)):

                word_slice = word[i:i+n]
                if not word_slice in ngrams:
                    ngrams[word_slice] = 1
                else:
                    ngrams[word_slice] += 1
        if j % (len(texts) // 10) == 0:
            print(round(j / len(texts) * 100, -1), "% done", sep='')

    return dict(sorted(ngrams.items(), key=lambda x:x[1], reverse=True))


def pad_word(word: str, texts: List[str], n: int):

    if n <= 0:
        return [word]

    ret = []
    for text in texts:
        new_word = word + " " + text
        ret += pad_word(new_word, texts, n - len(" " + text))

    return ret