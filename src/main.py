import json
import layout, analyzer

layouts = layout.load_dir('layouts')
data = json.load(open('data/200-data.json', 'r'))

results_L = []
results_R = []

for keys in layouts:
    counts = analyzer.count_trigrams(keys, data, thumb="LT")
    results_L.append(
        {
            'name': keys['name'],
            'data': counts,
        }
    )

for keys in layouts:
    counts = analyzer.count_trigrams(keys, data, thumb="RT")
    results_R.append(
        {
            'name': keys['name'],
            'data': counts,
        }
    )


results = []
for item_L, item_R in zip(results_L, results_R):
    if (item_L['name'] != item_R['name']):
        raise("ERROR")
        exit()
    else:
        results.append(
            {
                'name': item_L['name'],
                'data_L': item_L['data'],
                'data_R': item_R['data'],
            }
        )

trigram_type = 'onehand'
highest_to_lowest = True

results = sorted(results, key=lambda x : x['data_L'][trigram_type], reverse=highest_to_lowest)
print((trigram_type + " data:").ljust(27, ' '), 'Left    Right   Change')
for item in results:
    print(
        (item['name'] + ' ').ljust(25, '-'), 
        "{:.2%}".format(item['data_L'][trigram_type]).rjust(6, ' '),
        " ",
        "{:.2%}".format(item['data_R'][trigram_type]).rjust(6, ' '),
        "",
        "{:+.2%}".format(item['data_R'][trigram_type] - item['data_L'][trigram_type]).rjust(7, ' '),
    )