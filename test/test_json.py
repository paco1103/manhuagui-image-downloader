import json


data = {
    'downlist': [
        {'t': 0},
        {'t': 1}
    ]
}

with open('downlist.json', 'w') as f:
    json.dump('', f, ensure_ascii=False, indent=4)

data = 0
with open('downlist.json', 'r') as f:
    data = json.load(f)


print(data['downlist'])