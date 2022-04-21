import json
from typing import Union
from scripts.assignment import Assignment


def write_data(user_id: int, field: str, value: Union[str, int]) -> None:
    with open('./data.json') as f:
        data = json.load(f)

    user_id = str(user_id)

    if user_id not in data.keys():
        data[user_id] = {}

    data[user_id][field] = value

    with open('./data.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)


def write_assignment(user_id: int, assignment: Assignment) -> None:
    with open('./data.json') as f:
        data = json.load(f)

    user_id = str(user_id)

    if user_id not in data.keys():
        data[user_id] = {}

    pointer = data[user_id]

    for index, field in enumerate(assignment.get_path()):
        if index == len(assignment.get_path()) - 1:
            pointer.update({field: assignment.data})
        else:
            if field not in pointer.keys():
                pointer.update({field: {}})

            pointer = pointer[field]

    del pointer

    with open('./data.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)


def read_data(user_id: int) -> dict:
    with open('./data.json') as f:
        data = json.load(f)

        if str(user_id) in data.keys():
            return data[str(user_id)]
