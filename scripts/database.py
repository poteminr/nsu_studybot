import json
from typing import Union, Optional


def write_data(user_id: int, field: str, value: Union[str, int]) -> None:
    with open('./data.json') as f:
        data = json.load(f)

    user_id = str(user_id)

    if user_id not in data.keys():
        data[user_id] = {"assignments": {}}

    data[user_id][field] = value

    with open('./data.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)


def read_data(user_id: int) -> Optional[dict]:
    with open('./data.json') as f:
        data = json.load(f)

        if str(user_id) in data.keys():
            return data[str(user_id)]
        else:
            return None


def read_cities_data() -> dict:
    with open('data/cities.json') as f:
        data = json.load(f)

    return data
