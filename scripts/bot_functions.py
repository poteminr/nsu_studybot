import json
import datetime
from typing import Tuple, Optional, List, Union
from scripts.schedule_api import get_group_seminars, get_seminar_number, get_week_parity


def write_data(user_id: int, value, *fields):
    with open('./data.json') as f:
        data = json.load(f)

    user_id = str(user_id)

    if user_id not in data.keys():
        data[user_id] = {}

    pointer = data[user_id]

    for index, field in enumerate(fields):
        if index == len(fields) - 1:
            pointer.update({field: value})
        else:
            if field not in pointer.keys():
                pointer.update({field: {}})

            pointer = pointer[field]

    del pointer

    with open('./data.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)


def read_data(user_id: int):
    with open('./data.json') as f:
        data = json.load(f)

        if str(user_id) in data.keys():
            return data[str(user_id)]


def preprocess_date(date: datetime.datetime) -> Tuple[int, int, int]:
    print(type(date))
    weekday = date.weekday() + 1
    hour = date.hour + 7
    minute = date.minute

    if hour % 24 < hour:
        hour %= 24
        weekday += 1

    return weekday, hour, minute


def get_seminar_info_by_time(user_id: int, date: datetime.datetime) -> Tuple[Optional[str], List[int]]:
    user_group = read_data(user_id)['group']
    weekday, hour, minute = preprocess_date(date)

    _, schedule, seminar_weekdays = get_group_seminars(user_group)
    seminar_number = get_seminar_number(hour, minute)

    current_subject = None
    current_seminar_weekdays = None

    if weekday % 7 != 0:
        if seminar_number in schedule[weekday].keys():
            current_subject = schedule[weekday][seminar_number]
            current_seminar_weekdays = seminar_weekdays[current_subject]

    return current_subject, current_seminar_weekdays


def university_codes2text(code: str) -> str:
    university_codes = {"1.1": "НГУ", '1.2': "НГТУ",
                        "2.1": "МГУ", "2.2": "МГТУ"}

    return university_codes[code]


def university_codes2city(code: str) -> str:
    city_codes = {"1": "Новосибирск", "2": "Москва"}

    return city_codes[code.split(".")[0]]


def datetime2string(date: datetime.datetime) -> str:
    return f"{date.day}.{date.month}.{date.year}"


def get_date_of_lesson(current_date: datetime.datetime, lesson_weekday: int, return_datetime=False) -> Union[datetime.datetime, str]:
    current_weekday = current_date.weekday() + 1

    if get_week_parity() == 'even':
        current_weekday += 7

    if lesson_weekday > current_weekday:
        time_delta_days = lesson_weekday - current_weekday

    else:
        time_delta_days = 14 - current_weekday + lesson_weekday

    lesson_date = current_date + datetime.timedelta(days=time_delta_days)

    if return_datetime:
        return lesson_date
    else:
        return datetime2string(lesson_date)


def get_next_seminar_weekday_by_current_weekday(weekday: int, seminar_weekdays: List[int]) -> int:
    index_of_weekday = seminar_weekdays.index(weekday)

    if index_of_weekday + 1 >= len(seminar_weekdays):
        return seminar_weekdays[0]
    else:
        return seminar_weekdays[index_of_weekday + 1]


def get_next_seminar_date(current_date: datetime.datetime, seminar_weekdays: List[int]) -> datetime.datetime:
    current_weekday, _, _ = preprocess_date(current_date)

    if get_week_parity() == 'even':
        current_weekday += 7

    next_seminar_weekday = get_next_seminar_weekday_by_current_weekday(current_weekday, seminar_weekdays)
    next_seminar_datetime = get_date_of_lesson(current_date, next_seminar_weekday)

    return next_seminar_datetime


def generate_dates_of_future_seminars(date: datetime.datetime, seminar_weekdays: List[int], months=2) -> List[str]:
    future_seminars_dates = []

    for weekday in seminar_weekdays:
        future_date = get_date_of_lesson(date, weekday, return_datetime=True)
        future_seminars_dates.append(datetime2string(future_date))

        for factor in range(1, months + 1):
            future_date_with_period = future_date + datetime.timedelta(days=14*factor)
            future_seminars_dates.append(datetime2string(future_date_with_period))

    future_seminars_dates.sort(key=lambda d: datetime.datetime.strptime(d, "%d.%m.%Y"))

    return future_seminars_dates
