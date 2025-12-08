from datetime import datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup
from logger import create_logger

from .models import DaySchedule, FullCell, HalfCell, HourCell, ScheduleResponse
from .utils.parser_helpers import (
    _confirm_from_classes,
    _fmt_time,
    _has_disconnection,
    _inc_time,
    _safe_get_classes,
)

logger = create_logger(__name__)


def parse_schedule(
    html: str, address_name: str, max_days: Optional[int] = 2
) -> ScheduleResponse:
    soup = BeautifulSoup(html, "lxml")

    try:
        queue = next(
            q.get_text(strip=True)
            for q in soup.select("div.disconnection-detailed-table p")
        )
    except StopIteration:
        return ScheduleResponse(
            address=address_name,
            disconnection_queue="Немає інформації про чергу відключень",
            disconnections=[],
        )

    # Списки заголовков часов и дни в порядке появления
    hour_elems = soup.select(".disconnection-detailed-table-cell.head")
    hours = [h.get_text(strip=True) for h in hour_elems[:24]]  # максимум 24 часа

    day_elems = soup.select(".disconnection-detailed-table-cell.legend.day_col")
    day_names = [d.get_text(strip=True) for d in day_elems[:7]]  # максимум 7 дней

    cell_elems = soup.select(".disconnection-detailed-table-cell.cell")

    cell_index = 0
    days_to_parse = day_names if max_days is None else day_names[:max_days]

    disconnection_days = []

    for i, _ in enumerate(days_to_parse):
        day_date = (datetime.now() + timedelta(days=i)).date().isoformat()
        logger.info(f"Parsing schedule for date: {day_date}")

        day_rows = []
        day_has_disconnections = (
            False  # to track if any disconnections exist for the day
        )

        for hour_str in hours:
            # if no more cells — break safely
            if cell_index >= len(cell_elems):
                break

            cell = cell_elems[cell_index]
            cell_index += 1

            # full-hour classes
            cell_classes = _safe_get_classes(cell)
            full_off = _has_disconnection(cell_classes)
            full_confirm = _confirm_from_classes(cell_classes)

            # halves
            left_el = cell.select_one(".half.left")
            right_el = cell.select_one(".half.right")

            hr_parts = hour_str.split(":")
            try:
                base_h = int(hr_parts[0])
                base_m = int(hr_parts[1])
            except TypeError:
                base_h, base_m = 0, 0

            l_h, l_m = base_h, base_m
            l_e_h, l_e_m = _inc_time(base_h, base_m, 30)
            r_h, r_m = l_e_h, l_e_m
            r_e_h, r_e_m = _inc_time(base_h, base_m, 60)

            if full_off:
                day_has_disconnections = True
                halves = [
                    HalfCell(
                        start=_fmt_time(l_h, l_m),
                        end=_fmt_time(l_e_h, l_e_m),
                        off=True,
                        confirm=full_confirm,
                    ),
                    HalfCell(
                        start=_fmt_time(r_h, r_m),
                        end=_fmt_time(r_e_h, r_e_m),
                        off=True,
                        confirm=full_confirm,
                    ),
                ]
            else:
                if left_el:
                    left_classes = _safe_get_classes(left_el)
                    left_off = _has_disconnection(left_classes)
                    left_confirm = _confirm_from_classes(left_classes)
                else:
                    left_off, left_confirm = False, None

                if right_el:
                    right_classes = _safe_get_classes(right_el)
                    right_off = _has_disconnection(right_classes)
                    right_confirm = _confirm_from_classes(right_classes)
                else:
                    right_off, right_confirm = False, None

                if left_off or right_off:
                    day_has_disconnections = True

                halves = [
                    HalfCell(
                        start=_fmt_time(l_h, l_m),
                        end=_fmt_time(l_e_h, l_e_m),
                        off=left_off,
                        confirm=left_confirm,
                    ),
                    HalfCell(
                        start=_fmt_time(r_h, r_m),
                        end=_fmt_time(r_e_h, r_e_m),
                        off=right_off,
                        confirm=right_confirm,
                    ),
                ]

            both_halves_off = halves[0].off and halves[1].off
            inferred_full_off = full_off or both_halves_off

            hour_entry = HourCell(
                hour=hour_str,
                full=FullCell(off=bool(full_off), confirm=full_confirm),
                inferred_full_off=bool(inferred_full_off),
                halves=halves,
            )
            day_rows.append(hour_entry)

        disconnection_days.append(
            DaySchedule(
                date=day_date,
                has_disconnections=day_has_disconnections,
                cells=day_rows,
            )
        )

    formatted = {
        "address": address_name,
        "disconnection_queue": queue,
        "disconnections": disconnection_days,
    }

    return ScheduleResponse(**formatted)
