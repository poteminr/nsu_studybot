import json

def write_data(user_id, field, value):
    with open('data.json') as f:
        data = json.load(f)
    
    if str(user_id) not in data.keys():
        data[user_id] = {}
        data[user_id][field] = value 

    else:
        data[str(user_id)][field] = value

    with open('data.json', 'w') as f:
        json.dump(data, f)

def read_data(user_id):
    with open('data.json') as f:
        data = json.load(f)

    return data[str(user_id)]


def get_schedule(user_id, date):

    return "Мат.Анализ"
    