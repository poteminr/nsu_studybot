import requests
import json
from requests.auth import HTTPBasicAuth

with open('keys.json') as f:
    keys = json.load(f)

API_KEY = keys['NSU_API']


def get_group_id(group_number):
    method_url = f'https://table.nsu.ru/api/groups/search?name={group_number}'
    result = requests.get(method_url, auth=HTTPBasicAuth(API_KEY, ''))

    group_id = result.json()[0]['id']

    return group_id


def get_group_schedule(group_number):
    group_id = get_group_id(group_number)

    method_url = f'https://table.nsu.ru/api/schedules/search?id_group={group_id}'
    result = requests.get(method_url, auth=HTTPBasicAuth(API_KEY, ''))

    return result


def get_group_seminars(group_number):
    schedule = get_group_schedule(group_number).json()

    seminars_set = []
    seminars = {}

    for lesson in schedule:
        if lesson['type'] in ['пр', 'лаб']:
            seminars_set.append(lesson['name'])

            if lesson['weekday'] not in seminars.keys():
                seminars[lesson['weekday']] = {}

            seminars[lesson['weekday']][lesson['id_time']] = lesson['name']

    return list(set(seminars_set)), seminars


def get_seminar_times():
    method_url = 'https://table.nsu.ru/api/time'
    result = requests.get(method_url, auth=HTTPBasicAuth(API_KEY, ''))

    return result.json()


def get_time_by_id(id_time):
    result = get_seminar_times()

    seminar = result[id_time-1]
    start_time, end_time = seminar['begin'], seminar['end']

    return start_time, end_time


def get_parity():
    method_url = 'https://table.nsu.ru/api/parity'
    result = requests.get(method_url, auth=HTTPBasicAuth(API_KEY, ''))

    return result.json()['actual']