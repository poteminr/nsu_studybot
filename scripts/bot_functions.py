import json
import datetime
from typing import Tuple, Optional
from scripts.schedule_api import get_group_seminars, get_seminar_number


def write_data(user_id: int, field: str, value: Optional):
    with open('./data.json') as f:
        data = json.load(f)

    if str(user_id) not in data.keys():
        data[user_id] = {}
        data[user_id][field] = value

    else:
        data[str(user_id)][field] = value

    with open('./data.json', 'w') as f:
        json.dump(data, f)


def read_data(user_id: int):
    with open('./data.json') as f:
        data = json.load(f)

        if str(user_id) in data.keys():
            return data[str(user_id)]


def preprocess_date(date: datetime.datetime) -> Tuple[int, int, int]:
    weekday = datetime.date.weekday(date) + 1
    hour = date.hour + 7
    minute = date.minute

    if hour % 24 < hour:
        hour %= 24
        weekday += 1

    return weekday, hour, minute


def get_seminar_number_by_time(user_id: int, date: datetime.datetime) -> str:
    user_group = read_data(user_id)['group']
    weekday, hour, minute = preprocess_date(date)

    _, schedule = get_group_seminars(user_group)
    seminar_number = get_seminar_number(hour, minute)

    current_subject = None

    if weekday % 7 != 0:
        if seminar_number in schedule[weekday].keys():
            current_subject = schedule[weekday][seminar_number]

    return current_subject


def university_codes2text(code: str):
    university_codes = {"1.1": "НГУ", '1.2': "НГТУ",
                        "2.1": "МГУ", "2.2": "МГТУ"}

    return university_codes[code]


def university_codes2city(code: str):
    city_codes = {"1": "Новосибирск", "2": "Москва"}

    return city_codes[code.split(".")[0]]
