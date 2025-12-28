from datetime import datetime, timedelta

from logger import create_logger
from lxml import etree

from .models import DaySchedule, FullCell, HalfCell, HourCell, ScheduleResponse
from .utils.parser_helpers import (
    _confirm_from_classes,
    _fmt_time,
    _get_classes,
    _has_disconnection,
    _inc_time,
)

logger = create_logger(__name__)


def parse_schedule(
    html: str, address_name: str, max_days: int = 2
) -> ScheduleResponse:
    logger.debug("Starting parsing")


    tree = etree.HTML(html)
    queue_nodes = tree.xpath(
        "//div[contains(@class,'disconnection-detailed-table')]//p/text()"
    )
    logger.debug(queue_nodes)

    #* With new html structure it returns list of all p elements inside the parent div.
    # Like:
    # ["6.2 черга", "За Вашою адресою наразі не зафіксовано аварійних та планових відключень.", ...]
    # TODO: It can be useful to implement notifications based on outages in the exact moment.
    # For now we just take the first element as the queue info.
    if not queue_nodes:
        return ScheduleResponse(
            address=address_name,
            disconnection_queue="Немає інформації про чергу відключень",
            disconnections=[],
        )

    queue = queue_nodes[0].strip()

    # Hours in format "HH:00"
    hours = [f"{h:02d}:00" for h in range(24)]

    # Disconnection table cells
    cells = tree.xpath(
        "(//div[contains(@class, 'disconnection-detailed-table-container')])[1]"
        "/div[contains(concat(' ', normalize-space(@class), ' '), ' disconnection-detailed-table-cell ') "
        "and contains(concat(' ', normalize-space(@class), ' '), ' cell ')]"
    )

    cell_index = 0
    disconnection_days = []

    now = datetime.now()

    for day_offset in range(max_days):
        day_date = (now + timedelta(days=day_offset)).date().isoformat()
        logger.info(f"Parsing schedule for {address_name} for date: {day_date}")

        day_rows = []
        day_has_disconnections = False

        for hour_str in hours:
            if cell_index >= len(cells):
                break

            cell = cells[cell_index]
            cell_index += 1

            # Classes for full-hour
            cell_classes = _get_classes(cell)
            full_off = _has_disconnection(cell_classes)
            full_confirm = _confirm_from_classes(cell_classes)

            # TODO halves. With new HTML structure needs to be reworked.
            # TODO just don't have half elements in the new structure yet.
            left_el = cell.xpath(
                ".//div[contains(concat(' ', normalize-space(@class), ' '), ' half ') "
                "and contains(concat(' ', normalize-space(@class), ' '), ' left ')]"
            )
            right_el = cell.xpath(
                ".//div[contains(concat(' ', normalize-space(@class), ' '), ' half ') "
                "and contains(concat(' ', normalize-space(@class), ' '), ' right ')]"
            )

            left_el = left_el[0] if left_el else None
            right_el = right_el[0] if right_el else None

            try:
                base_h, base_m = map(int, hour_str.split(":"))
            except Exception:
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
                left_classes = _get_classes(left_el)
                right_classes = _get_classes(right_el)

                left_off = _has_disconnection(left_classes)
                left_confirm = _confirm_from_classes(left_classes)

                right_off = _has_disconnection(right_classes)
                right_confirm = _confirm_from_classes(right_classes)

                if left_off or right_off:
                    day_has_disconnections = True

                halves = [
                    HalfCell(
                        start=_fmt_time(l_h, l_m),
                        end=_fmt_time(l_e_h, l_e_m),
                        off=bool(left_off),
                        confirm=left_confirm,
                    ),
                    HalfCell(
                        start=_fmt_time(r_h, r_m),
                        end=_fmt_time(r_e_h, r_e_m),
                        off=bool(right_off),
                        confirm=right_confirm,
                    ),
                ]

            inferred_full_off = bool(full_off or (halves[0].off and halves[1].off))

            day_rows.append(
                HourCell(
                    hour=hour_str,
                    full=FullCell(off=bool(full_off), confirm=full_confirm),
                    inferred_full_off=inferred_full_off,
                    halves=halves,
                )
            )

        disconnection_days.append(
            DaySchedule(
                date=day_date,
                has_disconnections=day_has_disconnections,
                cells=day_rows,
            )
        )

    result = ScheduleResponse(
        address=address_name,
        disconnection_queue=queue,
        disconnections=disconnection_days,
    )

    logger.debug(result)
    return result
