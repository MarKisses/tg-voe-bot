from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from logger import create_logger

logger = create_logger(__name__)

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
    date: datetime
    has_disconnections: bool
    cells: List[HourCell]
    


class CurrentDisconnection(BaseModel):
    has_disconnection: bool
    is_emergency: bool | None
    reason: str | None
    started_at: datetime | None
    estimated_end: datetime | None


class ScheduleResponse(BaseModel):
    address: str
    disconnection_queue: str

    current_disconnection: CurrentDisconnection | None = None

    disconnections: List[DaySchedule]

    def get_day_schedule(self, date: datetime) -> Optional[DaySchedule]:
        for day in self.disconnections:
            logger.debug(f"Checking day schedule for date: {day.date} against {date}")
            if day.date.date() == date.date():
                return day
        return None
