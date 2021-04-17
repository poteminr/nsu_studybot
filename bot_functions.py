import json
import datetime
from schedule_api import get_group_seminars, get_time_by_id


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


# def get_next_lesson_date(user_id, field):
#     next_lesson_date = '24.05.2021 9:00'
    
#     return next_lesson_date


def get_seminar_number(hour, minute):
    number = None
    for lesson in range(1, 6):
        start_time, end_time = get_time_by_id(lesson)

        h_start, m_start = int(start_time.split(':')[0]), int(start_time.split(':')[1])
        h_end, m_end = int(end_time.split(':')[0]), int(end_time.split(':')[1])


        start = datetime.datetime(2021, 1, 1, h_start, m_start)
        end = datetime.datetime(2021, 1, 1, h_end, m_end) + datetime.timedelta(minutes=5)

        current = datetime.datetime(2021, 1, 1, hour, minute)

        if (start < current) and (current < end):
            number = lesson
            break
    
    return number

def get_seminar_by_time(user_id, date):
    user_group = read_data(user_id)['group']
    weekday = datetime.date.weekday(date) + 1
    hour = date.hour + 7
    minute = date.minute

    if hour % 24 < hour:
        hour %= 24
        weekday += 1

    _, schedule = get_group_seminars(user_group)
    seminar_number = get_seminar_number(hour, minute)

    current_subject = None

    if weekday % 7 !=0:
        if seminar_number in schedule[weekday].keys():
            current_subject = schedule[weekday][seminar_number]
            # next_lesson_date = get_next_lesson_date(user_id, current_subject)

    return current_subject
    