import json
from typing import Union, Optional
import glob


def write_data(user_id: int, field: str, value: Union[str, int]) -> None:
    if f"data/{user_id}.json" not in glob.glob("data/*.json"):
        with open(f"data/{user_id}.json", "w") as f:
            json.dump({"assignments": {}}, f)

    with open(f"data/{user_id}.json") as f:
        user_data = json.load(f)

    user_data[field] = value

    with open(f"data/{user_id}.json", 'w') as f:
        json.dump(user_data, f, ensure_ascii=False)


def read_data(user_id: int) -> Optional[dict]:
    if f"data/{user_id}.json" in glob.glob("data/*.json"):
        with open(f"data/{user_id}.json") as f:
            user_data = json.load(f)

        return user_data
    else:
        return None


def read_cities_data() -> dict:
    with open('data/cities.json') as f:
        data = json.load(f)

    return data
