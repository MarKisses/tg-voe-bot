from datetime import datetime

from logger import create_logger
from pydantic import ValidationError

from .models import (
    DaySchedule,
    FullCell,
    HalfCell,
    HourCell,
    ScheduleResponse,
)
from .models.api_models import ApiCell, ApiSearchResponse, ApiTable
from .utils.parser_helpers import (
    confirm_from_classes,
    current_disconnection_info,
    fmt_time,
    inc_time,
    overlaps,
    segment_confirm,
    segment_is_off,
    segment_minutes,
)

logger = create_logger(__name__)

NO_QUEUE_INFO = "Немає інформації про чергу відключень"


def _empty_response(address_name: str, queue: str = NO_QUEUE_INFO) -> ScheduleResponse:
    return ScheduleResponse(
        address=address_name,
        disconnection_queue=queue,
        disconnections=[],
        current_disconnection=None,
    )


def _queue_from_table(table: ApiTable) -> str:
    queue = table.listnum
    if queue is None and table.message:
        queue = table.message.queue
    if queue is None:
        return NO_QUEUE_INFO
    return f"{queue} черга"


def _parse_cell(cell: ApiCell, hour_index: int) -> HourCell:
    base_h = hour_index
    hour_str = fmt_time(base_h, 0)

    l_h, l_m = base_h, 0
    r_h, r_m = inc_time(base_h, 0, 30)
    e_h, e_m = inc_time(base_h, 0, 60)

    # (start_min, end_min) for left and right halves of the hour
    half_bounds = [(0, 30), (30, 60)]
    half_off = [False, False]
    half_confirm: list[bool | None] = [None, None]

    for segment in cell.segments:
        if not segment_is_off(segment):
            continue

        start_min, end_min = segment_minutes(segment)
        if end_min <= start_min:
            continue

        confirm = segment_confirm(segment)
        for i, (h_start, h_end) in enumerate(half_bounds):
            if overlaps(h_start, h_end, start_min, end_min):
                half_off[i] = True
                # Confirmed segment wins over unconfirmed one in the same half
                if confirm or half_confirm[i] is None:
                    half_confirm[i] = confirm

    halves = [
        HalfCell(
            start=fmt_time(l_h, l_m),
            end=fmt_time(r_h, r_m),
            off=half_off[0],
            confirm=half_confirm[0],
        ),
        HalfCell(
            start=fmt_time(r_h, r_m),
            end=fmt_time(e_h, e_m),
            off=half_off[1],
            confirm=half_confirm[1],
        ),
    ]

    full_off = all(half_off)
    full_confirm = None
    if full_off:
        full_confirm = (
            bool(half_confirm[0] and half_confirm[1])
            if None not in half_confirm
            else confirm_from_classes(cell.class_.split())
        )

    return HourCell(
        hour=hour_str,
        full=FullCell(off=full_off, confirm=full_confirm),
        halves=halves,
    )


def parse_schedule(
    data: dict | None, address_name: str, max_days: int = 2
) -> ScheduleResponse:
    logger.debug("Starting parsing")

    if not data:
        return _empty_response(address_name)

    try:
        response = ApiSearchResponse.model_validate(data)
    except ValidationError as e:
        logger.error(f"Unexpected search response format for {address_name}: {e}")
        return _empty_response(address_name)

    if not response.ok or not response.tables:
        logger.warning(f"No tables in search response for {address_name}: {data}")
        return _empty_response(address_name)

    if isinstance(response.addresses, dict) and len(response.addresses) > 1:
        # Several EIC on the same address. Site asks to pick one via selected_eic.
        logger.warning(
            f"Several addresses found for {address_name}: {response.addresses}. "
            "Using the first table."
        )
    if len(response.tables) > 1:
        logger.warning(
            f"{len(response.tables)} tables found for {address_name}. Using the first one."
        )

    table = response.tables[0]
    queue = _queue_from_table(table)
    current_disconnection = current_disconnection_info(table.message)

    if table.empty or not table.rows:
        logger.info(f"Empty schedule table for {address_name}.")
        return ScheduleResponse(
            address=address_name,
            disconnection_queue=queue,
            disconnections=[],
            current_disconnection=current_disconnection,
        )

    disconnection_days = []

    for row in table.rows[:max_days]:
        logger.info(f"Parsing schedule for {address_name} for date: {row.date}")

        if len(row.cells) != 24:
            logger.warning(f"Row {row.date} has {len(row.cells)} cells instead of 24")

        day_rows = [_parse_cell(cell, i) for i, cell in enumerate(row.cells[:24])]

        disconnection_days.append(
            DaySchedule(
                date=datetime.combine(row.date, datetime.min.time()),
                has_disconnections=any(
                    half.off for hour in day_rows for half in hour.halves
                ),
                cells=day_rows,
            )
        )

    if not any(day.has_disconnections for day in disconnection_days):
        logger.info(
            f"No disconnections found for {address_name} for the next {max_days} days."
        )
        return ScheduleResponse(
            current_disconnection=current_disconnection,
            address=address_name,
            disconnection_queue=queue,
            disconnections=[],
        )

    result = ScheduleResponse(
        current_disconnection=current_disconnection,
        address=address_name,
        disconnection_queue=queue,
        disconnections=disconnection_days,
    )

    logger.debug(result)
    return result
