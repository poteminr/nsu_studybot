import datetime
from typing import Tuple, Optional, List, Union
from scripts.schedule_api import get_group_seminars, get_seminar_number, get_week_parity
from scripts.database import read_data


def convert_utc_to_local_time(date: datetime.datetime, utc_delta: int = 7):
    return date + datetime.timedelta(hours=utc_delta)


def process_date(date: datetime.datetime) -> Tuple[int, int, int]:
    weekday = date.weekday() + 1  # [0, 6] -> [1, 7]
    hour = date.hour
    minute = date.minute

    if get_week_parity() == 'even':
        weekday += 7

    return weekday, hour, minute


def get_seminar_info_by_time(user_id: int, date: datetime.datetime) -> Tuple[Optional[str], List[int]]:
    user_data = read_data(user_id)
    user_group = user_data['group']

    weekday, hour, minute = process_date(date)

    _, schedule, seminar_weekdays = get_group_seminars(user_group)
    seminar_number = get_seminar_number(hour, minute)

    current_subject = None
    current_seminar_weekdays = None

    if weekday % 7 != 0:
        if seminar_number in schedule[weekday].keys():
            current_subject = schedule[weekday][seminar_number]
            current_seminar_weekdays = seminar_weekdays[current_subject]

    return current_subject, current_seminar_weekdays


def datetime2string(date: datetime.datetime) -> str:
    return f"{date.day}.{date.month}.{date.year}"


def get_nearest_date_of_weekday(current_date: datetime.datetime, target_weekday: int, return_datetime=False) -> Union[datetime.datetime, str]:
    current_weekday, _, _ = process_date(current_date)

    if target_weekday > current_weekday:
        time_delta_days = target_weekday - current_weekday

    else:
        time_delta_days = 14 - current_weekday + target_weekday

    target_date = current_date + datetime.timedelta(days=time_delta_days)

    if return_datetime:
        return target_date
    else:
        return datetime2string(target_date)


def get_next_seminar_weekday_by_current_weekday(weekday: int, seminar_weekdays: List[int]) -> int:
    index_of_weekday = seminar_weekdays.index(weekday)

    if index_of_weekday + 1 >= len(seminar_weekdays):
        return seminar_weekdays[0]
    else:
        return seminar_weekdays[index_of_weekday + 1]


def get_next_seminar_date(current_date: datetime.datetime, seminar_weekdays: List[int]) -> datetime.datetime:
    current_weekday, _, _ = process_date(current_date)

    next_seminar_weekday = get_next_seminar_weekday_by_current_weekday(current_weekday, seminar_weekdays)
    next_seminar_datetime = get_nearest_date_of_weekday(current_date, next_seminar_weekday)

    return next_seminar_datetime


def generate_dates_of_future_seminars(date: datetime.datetime, seminar_weekdays: List[int], months=2) -> List[str]:
    future_seminars_dates = []

    for weekday in seminar_weekdays:
        future_date = get_nearest_date_of_weekday(date, weekday, return_datetime=True)
        future_seminars_dates.append(datetime2string(future_date))

        for factor in range(1, months + 1):
            future_date_with_period = future_date + datetime.timedelta(days=14 * factor)
            future_seminars_dates.append(datetime2string(future_date_with_period))

    future_seminars_dates.sort(key=lambda d: datetime.datetime.strptime(d, "%d.%m.%Y"))

    return future_seminars_dates


def university_codes2text(code: str) -> str:
    university_codes = {"1.1": "НГУ", '1.2': "НГТУ",
                        "2.1": "МГУ", "2.2": "МГТУ"}

    return university_codes[code]


def university_codes2city(code: str) -> str:
    city_codes = {"1": "Новосибирск", "2": "Москва"}

    return city_codes[code.split(".")[0]]


def get_utc_delta_by_city(city: str) -> int:
    city_timezones = {"Новосибирск": 7}

    return city_timezones[city]
