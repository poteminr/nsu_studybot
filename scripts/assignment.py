from dataclasses import dataclass
from typing import List, Union
from telegram import Message


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
