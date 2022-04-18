import json
from typing import Union


def write_data(user_id: int, value: Union[str, int], *fields: str) -> None:
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


def read_data(user_id: int) -> dict:
    with open('./data.json') as f:
        data = json.load(f)

        if str(user_id) in data.keys():
            print(data[str(user_id)], type(data[str(user_id)]))
            return data[str(user_id)]
