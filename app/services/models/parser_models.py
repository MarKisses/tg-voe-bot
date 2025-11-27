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
    inferred_full_off: bool
    halves: List[HalfCell]


class DaySchedule(BaseModel):
    date: str
    has_disconnections: bool
    cells: List[HourCell]


class ScheduleResponse(BaseModel):
    address: str
    disconnection_queue: str
    disconnections: List[DaySchedule]
