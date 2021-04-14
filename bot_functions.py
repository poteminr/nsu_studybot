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


def get_next_lesson_date(user_id, field):
    next_lesson_date = '24.05.2021 9:00'
    
    return next_lesson_date


def get_schedule(user_id, date):
    current_subject = 'Мат. Анализ'
    next_lesson_date = get_next_lesson_date(user_id, current_subject)

    return current_subject, next_lesson_date
    