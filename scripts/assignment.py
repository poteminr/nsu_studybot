from dataclasses import dataclass
from typing import List, Union, Optional
from telegram import Message
import json


@dataclass
class Assignment:
    seminar_name: str = None
    date: str = None
    assignment_type: str = None
    text_data: str = None
    photo_data: str = None
    future_seminars_dates: List[str] = None

    def get_message_after_uploading(self) -> str:
        if self.assignment_type == 'photo':
            return f"Фотография '{self.seminar_name}' на {self.date} успешно загружена!"
        else:
            return f"Задание по '{self.seminar_name}' на {self.date} успешно загружено!"

    def get_message_after_deleting(self) -> str:
        return f"Задание по '{self.seminar_name}' на {self.date} успешно удалено!"

    @staticmethod
    def _parse_text(text: str) -> Optional[str]:
        text = text.strip()
        if text != "/add":
            return text.split("/add")[1].strip()
        else:
            return None

    def parse_message(self, message: Message) -> None:
        if len(message.photo) == 0:
            self.assignment_type = 'text'
            self.text_data = self._parse_text(message.text)
        else:
            self.assignment_type = 'photo'
            self.photo_data = message.photo[-1]['file_id']
            if message.caption is not None:
                self.text_data = self._parse_text(message.caption)

    def _create_dict_with_data(self) -> dict:
        if all([self.photo_data, self.text_data]):
            return {"photo": self.photo_data, "text": self.text_data}

        elif self.photo_data is not None:
            return {"photo": self.photo_data}

        elif self.text_data is not None:
            return {"text": self.text_data}

    def _get_path(self) -> List[Optional[str]]:
        return [self.seminar_name, self.date]

    def upload_to_database(self, user_id: int, database_path: str = './data.json') -> None:
        with open(database_path) as f:
            data = json.load(f)

        user_id = str(user_id)
        if user_id not in data.keys():
            data[user_id] = {}

        pointer = data[user_id]
        for ind, field in enumerate(self._get_path()):
            if ind == len(self._get_path()) - 1:
                pointer.update({field: self._create_dict_with_data()})
            else:
                if field not in pointer.keys():
                    pointer.update({field: {}})

                pointer = pointer[field]

        del pointer

        with open(database_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False)

    def remove_from_database(self, user_id: int, database_path: str = './data.json'):
        with open(database_path) as f:
            data = json.load(f)

        user_id = str(user_id)

        if len(data[user_id][self.seminar_name].keys()) == 1:
            data[user_id].pop(self.seminar_name)
        else:
            data[user_id][self.seminar_name].pop(self.date)

        with open(database_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False)
