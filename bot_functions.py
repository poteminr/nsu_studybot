import json
import datetime
from schedule_api import get_group_seminars, get_time_by_id, get_seminar_times


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


def get_seminar_number(hour, minute):
    number = None
    seminars = get_seminar_times()

    for sem_id, seminar in enumerate(seminars):
        start_time, end_time = seminar['begin'], seminar['end']

        h_start, m_start = int(start_time.split(':')[0]), int(start_time.split(':')[1])
        h_end, m_end = int(end_time.split(':')[0]), int(end_time.split(':')[1])

        start = datetime.datetime(2021, 1, 1, h_start, m_start)
        end = datetime.datetime(2021, 1, 1, h_end, m_end) + datetime.timedelta(minutes=5)

        current = datetime.datetime(2021, 1, 1, hour, minute)

        if (start < current) and (current < end):
            number = sem_id + 1
            break

    return number


def preprocess_date(date):
    weekday = datetime.date.weekday(date) + 1
    hour = date.hour + 7
    minute = date.minute

    if hour % 24 < hour:
        hour %= 24
        weekday += 1

    return weekday, hour, minute


def get_seminar_number_by_time(user_id, date):
    user_group = read_data(user_id)['group']
    weekday, hour, minute = preprocess_date(date)

    _, schedule = get_group_seminars(user_group)
    seminar_number = get_seminar_number(hour, minute)

    current_subject = None

    if weekday % 7 != 0:
        if seminar_number in schedule[weekday].keys():
            current_subject = schedule[weekday][seminar_number]

    return current_subject
