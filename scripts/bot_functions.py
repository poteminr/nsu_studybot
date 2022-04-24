import datetime
from typing import Tuple, Optional, List, Union
from scripts.schedule_api import get_group_seminars, get_seminar_number, get_week_parity


def convert_utc_to_local_time(date: datetime.datetime, utc_delta: int = 7):
    return date + datetime.timedelta(hours=utc_delta)


def extract_time_data(date: datetime.datetime) -> Tuple[int, int, int]:
    weekday = date.weekday() + 1  # [0, 6] -> [1, 7]
    hour = date.hour
    minute = date.minute

    if get_week_parity() == 'even':
        weekday += 7

    return weekday, hour, minute


def get_current_seminar(user_group: int, date: datetime.datetime) -> Tuple[Optional[str], Optional[List[int]]]:
    current_seminar_name = None
    current_seminar_weekdays = None

    current_weekday, current_hour, current_minute = extract_time_data(date)

    if current_weekday % 7 != 0:
        _, schedule, seminar_weekdays = get_group_seminars(user_group)
        seminar_number = get_seminar_number(current_hour, current_minute)

        if seminar_number in schedule[current_weekday].keys():
            current_seminar_name = schedule[current_weekday][seminar_number]
            current_seminar_weekdays = seminar_weekdays[current_seminar_name]

    return current_seminar_name, current_seminar_weekdays


def format_datetime(date: datetime.datetime) -> str:
    return f"{date.day}.{date.month}.{date.year}"


def _get_nearest_date_of_weekday(current_date: datetime.datetime, target_weekday: int, return_datetime: bool = False) -> Union[datetime.datetime, str]:
    current_weekday, _, _ = extract_time_data(current_date)

    if target_weekday > current_weekday:
        time_delta_days = target_weekday - current_weekday

    else:
        time_delta_days = 14 - current_weekday + target_weekday

    target_date = current_date + datetime.timedelta(days=time_delta_days)

    if return_datetime:
        return target_date
    else:
        return format_datetime(target_date)


def _get_next_seminar_weekday_by_current_weekday(weekday: int, seminar_weekdays: List[int]) -> int:
    index_of_weekday = seminar_weekdays.index(weekday)

    if index_of_weekday + 1 >= len(seminar_weekdays):
        return seminar_weekdays[0]
    else:
        return seminar_weekdays[index_of_weekday + 1]


def _get_next_seminar_date(current_date: datetime.datetime, seminar_weekdays: List[int]) -> datetime.datetime:
    current_weekday, _, _ = extract_time_data(current_date)

    next_seminar_weekday = _get_next_seminar_weekday_by_current_weekday(current_weekday, seminar_weekdays)
    next_seminar_datetime = _get_nearest_date_of_weekday(current_date, next_seminar_weekday)

    return next_seminar_datetime


def generate_dates_of_future_seminars(date: datetime.datetime, seminar_weekdays: List[int], months=2) -> List[str]:
    future_seminars_dates = []

    for weekday in seminar_weekdays:
        future_date = _get_nearest_date_of_weekday(date, weekday, return_datetime=True)
        future_seminars_dates.append(format_datetime(future_date))

        for factor in range(1, months + 1):
            future_date_with_period = future_date + datetime.timedelta(days=14 * factor)
            future_seminars_dates.append(format_datetime(future_date_with_period))

    future_seminars_dates.sort(key=lambda d: datetime.datetime.strptime(d, "%d.%m.%Y"))

    return future_seminars_dates


def university_code2text(code: str) -> str:
    university_codes = {"1.1": "НГУ", '1.2': "НГТУ",
                        "2.1": "МГУ", "2.2": "МГТУ"}

    return university_codes[code]
