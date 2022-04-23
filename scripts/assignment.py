from dataclasses import dataclass
from typing import List, Union
from telegram import Message
import json


@dataclass
class Assignment:
    seminar_name: str = None
    date: str = None
    assignment_type: str = None
    data: str = None
    future_seminars_dates: List[str] = None

    def get_path(self) -> List[Union[str, None]]:
        return [self.seminar_name, self.date]

    def get_text_for_reply(self) -> str:
        if self.assignment_type == "photo":
            return f"Фотография '{self.seminar_name}' на {self.date} успешно загружена!"
        else:
            return f"Задание по '{self.seminar_name}' на {self.date} успешно загружено!"

    def parse_message(self, message: Message) -> None:
        if len(message.photo) == 0:
            self.assignment_type = 'text'
            self.data = message.text.split("/add")[1].strip()
        else:
            self.assignment_type = 'photo'
            self.data = message.photo[-1]['file_id']

    def upload_to_database(self, user_id: int, database_path: str = './data.json') -> None:
        with open(database_path) as f:
            data = json.load(f)

        user_id = str(user_id)
        if user_id not in data.keys():
            data[user_id] = {}

        pointer = data[user_id]
        for index, field in enumerate(self.get_path()):
            if index == len(self.get_path()) - 1:
                pointer.update({field: self.data})
            else:
                if field not in pointer.keys():
                    pointer.update({field: {}})

                pointer = pointer[field]

        del pointer

        with open(database_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False)
