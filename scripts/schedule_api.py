import requests
from requests.auth import HTTPBasicAuth
from typing import List, Tuple, Dict
import datetime
from scripts.private_keys import import_private_keys

API_KEY = import_private_keys(json_path='./keys.json', key_name='NSU_API')


def get_group_id(group_number: int) -> int:
    method_url = f'https://table.nsu.ru/api/groups/search?name={group_number}'
    result = requests.get(method_url, auth=HTTPBasicAuth(API_KEY, ''))

    group_id = result.json()[0]['id']

    return group_id


def get_group_schedule(group_number: int) -> List:
    group_id = get_group_id(group_number)

    method_url = f'https://table.nsu.ru/api/schedules/search?id_group={group_id}'
    group_schedule = requests.get(method_url, auth=HTTPBasicAuth(API_KEY, ''))

    return group_schedule.json()


def get_bells_schedule():
    # return list with dicts
    method_url = 'https://table.nsu.ru/api/time'
    result = requests.get(method_url, auth=HTTPBasicAuth(API_KEY, ''))

    return result.json()


def get_time_by_seminar_number(seminar_number: int) -> Tuple[str, str]:
    result = get_bells_schedule()

    seminar = result[seminar_number - 1]
    start_time, end_time = seminar['begin'], seminar['end']

    return start_time, end_time


def get_seminar_number(hour: int, minute: int) -> int:
    number = None
    seminars = get_bells_schedule()

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


def get_week_parity() -> str:
    method_url = 'https://table.nsu.ru/api/parity'
    result = requests.get(method_url, auth=HTTPBasicAuth(API_KEY, ''))

    return result.json()['actual']


def get_group_seminars(group_number: int) -> Tuple[List[str], Dict[int, Dict[int, str]], Dict[str, List[int]]]:
    schedule = get_group_schedule(group_number)

    list_of_all_seminars = []
    seminars = {}
    seminars_weekdays = {}

    for lesson in schedule:
        if lesson['type'] in ['пр', 'лаб']:
            weekday = lesson['weekday']
            id_time = lesson['id_time']
            name = lesson['name']

            if name not in seminars_weekdays.keys():
                seminars_weekdays[name] = []

            if weekday not in seminars.keys():
                seminars[weekday] = {}

            seminars[weekday][id_time] = name
            seminars_weekdays[name].append(weekday)
            list_of_all_seminars.append(name)

    return list(set(list_of_all_seminars)), seminars, seminars_weekdays
