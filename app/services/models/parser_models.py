from typing import List, Optional

from pydantic import BaseModel


class HalfCell(BaseModel):
    start: str
    end: str
    off: bool | None
    confirm: Optional[bool]


class FullCell(BaseModel):
    off: bool | None
    confirm: Optional[bool]


class HourCell(BaseModel):
    hour: str
    full: FullCell
    halves: List[HalfCell]


class DaySchedule(BaseModel):
    date: str
    has_disconnections: bool
    cells: List[HourCell]


class ScheduleResponse(BaseModel):
    address: str
    disconnection_queue: str
    disconnections: List[DaySchedule]
    
    def get_day_schedule(self, date: str) -> Optional[DaySchedule]:
        for day in self.disconnections:
            if day.date == date:
                return day
        return None
