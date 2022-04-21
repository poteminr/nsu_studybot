from dataclasses import dataclass
from typing import List


@dataclass
class Assignment:
    seminar_name: str = None
    date: str = None
    assignment_type: str = None
    data: str = None
    future_seminars_dates: List[str] = None

    def get_path(self):
        return [self.seminar_name, self.date]

    def get_text_for_reply(self):
        if self.assignment_type == "photo":
            return f"Фотография '{self.seminar_name}' на {self.date} успешно загружена!"
        else:
            return f"Задание по '{self.seminar_name}' на {self.date} успешно загружено!"
