from dataclasses import dataclass
from typing import List, Union, Optional
from telegram import Message
import json


@dataclass
class Assignment:
    seminar_name: str = None
    date: str = None
    text_data: str = None
    photo_data: str = None
    future_seminars_dates: List[str] = None

    @property
    def message_after_uploading(self) -> str:
        return f"Задание по '{self.seminar_name}' на {self.date} успешно загружено!"

    @property
    def message_after_deleting(self) -> str:
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
            self.text_data = self._parse_text(message.text)
        else:
            self.photo_data = message.photo[-1]['file_id']
            if message.caption is not None:
                self.text_data = self._parse_text(message.caption)

    def _create_dict_with_data(self) -> dict:
        if all([self.photo_data, self.text_data]):
            return {"photo_data": self.photo_data, "text_data": self.text_data}

        elif self.photo_data is not None:
            return {"photo_data": self.photo_data}

        elif self.text_data is not None:
            return {"text_data": self.text_data}

    def _get_path(self) -> List[Optional[str]]:
        return ['assignments', self.seminar_name, self.date]

    def upload_to_database(self, user_id: int, database_directory: str = 'data/') -> None:
        with open(f"{database_directory}{user_id}.json") as f:
            user_data = json.load(f)

        pointer = user_data
        for ind, field in enumerate(self._get_path()):
            if ind == len(self._get_path()) - 1:
                pointer.update({field: self._create_dict_with_data()})
            else:
                if field not in pointer.keys():
                    pointer.update({field: {}})

                pointer = pointer[field]

        del pointer

        with open(f"{database_directory}{user_id}.json", 'w') as f:
            json.dump(user_data, f, ensure_ascii=False)

    def remove_from_database(self, user_id: int, database_directory: str = 'data/') -> None:
        with open(f"{database_directory}{user_id}.json") as f:
            user_data = json.load(f)

        if len(user_data['assignments'][self.seminar_name].keys()) == 1:
            user_data['assignments'].pop(self.seminar_name)
        else:
            user_data['assignments'][self.seminar_name].pop(self.date)

        with open(f"{database_directory}{user_id}.json", 'w') as f:
            json.dump(user_data, f, ensure_ascii=False)

    def to_string(self) -> [str, str]:
        if self.photo_data is not None:
            data_type = "photo"
            text = f"{self.date}" \
                   f"\n{len(self.date) * '-'}"\
                   f"\n{self.seminar_name}" \
                   f"\n{len(self.seminar_name) * '-'}" \

            if self.text_data is not None:
                text += f"\n\n Подпись: {self.text_data}"
        else:
            data_type = "text"
            text = f"*{self.date}*" \
                   f"\n{len(self.date) * '-'}" \
                   f"\n*{self.seminar_name}*" \
                   f"\n{len(self.seminar_name) * '-'}" \
                   f"\n\n{self.text_data}"

        return text, data_type
