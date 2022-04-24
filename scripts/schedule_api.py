import requests
from requests.auth import HTTPBasicAuth
from typing import List, Tuple, Dict, Union
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


def get_bells_schedule() -> List[Dict[str, Union[str, int]]]:
    method_url = 'https://table.nsu.ru/api/time'
    result = requests.get(method_url, auth=HTTPBasicAuth(API_KEY, ''))

    return result.json()


def get_time_by_seminar_number(seminar_number: int) -> Tuple[str, str]:
    result = get_bells_schedule()

    seminar = result[seminar_number - 1]
    start_time, end_time = seminar['begin'], seminar['end']

    return start_time, end_time


def get_seminar_number(current_hour: int, current_minute: int) -> int:
    number = None
    seminars = get_bells_schedule()

    for seminar_index, seminar in enumerate(seminars):
        start_time = seminar['begin'].split(':')
        end_time = seminar['end'].split(':')

        hour_start, minute_start = int(start_time[0]), int(start_time[1])
        hour_end, minute_end = int(end_time[0]), int(end_time[1])

        seminar_start_time = datetime.datetime(2021, 1, 1, hour_start, minute_start)
        seminar_end_time = datetime.datetime(2021, 1, 1, hour_end, minute_end) + datetime.timedelta(minutes=5)
        current_time = datetime.datetime(2021, 1, 1, current_hour, current_minute)

        if (seminar_start_time < current_time) and (current_time < seminar_end_time):
            number = seminar_index + 1
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

    for seminar in schedule:
        if seminar['type'] in ['пр', 'лаб']:
            weekday = seminar['weekday']
            id_time = seminar['id_time']
            seminar_name = seminar['name']

            if seminar_name not in seminars_weekdays.keys():
                seminars_weekdays[seminar_name] = []

            if weekday not in seminars.keys():
                seminars[weekday] = {}

            seminars[weekday][id_time] = seminar_name
            seminars_weekdays[seminar_name].append(weekday)
            list_of_all_seminars.append(seminar_name)

    return list(set(list_of_all_seminars)), seminars, seminars_weekdays
