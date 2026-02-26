from logger import create_logger
from lxml import etree

from .models import (
    CurrentDisconnection,
    DaySchedule,
    FullCell,
    HalfCell,
    HourCell,
    ScheduleResponse,
)
from .utils.parser_helpers import (
    confirm_from_classes,
    current_disconnection_info,
    fmt_time,
    get_classes,
    has_disconnection,
    has_full_disconnection,
    inc_time,
    parse_css_var,
    parse_day_label,
)

logger = create_logger(__name__)


def parse_schedule(html: str, address_name: str, max_days: int = 2) -> ScheduleResponse:
    logger.debug("Starting parsing")

    tree = etree.HTML(html)
    queue_nodes = tree.xpath(
        "//div[contains(@class,'disconnection-detailed-table')]//p//text()"
    )
    logger.debug(queue_nodes)

    # * With new html structure it returns list of all p elements inside the parent div.
    # Like:
    # ["6.2 черга", "За Вашою адресою наразі не зафіксовано аварійних та планових відключень.", ...]
    # TODO: It can be useful to implement notifications based on outages in the exact moment.
    # For now we just take the first element as the queue info.
    if not queue_nodes:
        return ScheduleResponse(
            address=address_name,
            disconnection_queue="Немає інформації про чергу відключень",
            disconnections=[],
            current_disconnection=None,
        )

    queue = queue_nodes[0].strip()
    queue_nodes = [node.strip() for node in queue_nodes]
    current_disconnection: CurrentDisconnection = current_disconnection_info(
        queue_nodes[1:]
    )

    days = tree.xpath(
        "(//div[contains(@class, 'disconnection-detailed-table-container')])[1]"
        "/div[contains(@class, 'day_col')]"
        "/text()"
    )

    if not days:
        logger.warning(f"No day columns found in the schedule for {address_name}.")
        return ScheduleResponse(
            address=address_name,
            disconnection_queue=queue,
            disconnections=[],
            current_disconnection=None,
        )

    day_dates = [parse_day_label(day) for day in days]

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

    for day_date in day_dates:
        logger.info(f"Parsing schedule for {address_name} for date: {day_date}")

        day_rows = []
        day_has_disconnections = False

        for hour_str in hours:
            if cell_index >= len(cells):
                break

            cell = cells[cell_index]
            cell_index += 1

            # Classes for full-hour
            cell_classes = get_classes(cell)
            full_off = has_full_disconnection(cell_classes)
            partially_off = has_disconnection(cell_classes)
            confirm_disconnection = confirm_from_classes(cell_classes)

            # TODO halves. НАДО ПРИЧЕСАТЬ!
            fill_el = cell.xpath(
                ".//div[contains(concat(' ', normalize-space(@class), ' '), ' fill ')]"
            )

            fill_el = fill_el[0] if fill_el else None

            try:
                base_h, base_m = map(int, hour_str.split(":"))
            except Exception:
                base_h, base_m = 0, 0

            l_h, l_m = base_h, base_m
            l_e_h, l_e_m = inc_time(base_h, base_m, 30)
            r_h, r_m = l_e_h, l_e_m
            r_e_h, r_e_m = inc_time(base_h, base_m, 60)

            if full_off:
                day_has_disconnections = True
                halves = [
                    HalfCell(
                        start=fmt_time(l_h, l_m),
                        end=fmt_time(l_e_h, l_e_m),
                        off=True,
                        confirm=confirm_disconnection,
                    ),
                    HalfCell(
                        start=fmt_time(r_h, r_m),
                        end=fmt_time(r_e_h, r_e_m),
                        off=True,
                        confirm=confirm_disconnection,
                    ),
                ]
            elif partially_off:
                left_off = right_off = False
                confirmed = None

                if fill_el is not None:
                    style = fill_el.attrib.get("style", "")
                    start_pct = parse_css_var(style, "start") or 0
                    size_pct = parse_css_var(style, "size") or 0

                    start_min = int(start_pct * 60 / 100)
                    end_min = min(60, int((start_pct + size_pct) * 60 / 100))

                    def overlaps(a_start, a_end, b_start, b_end):
                        return b_start < a_end and b_end > a_start

                    left_off = overlaps(0, 30, start_min, end_min)
                    right_off = overlaps(30, 60, start_min, end_min)

                    confirmed = confirm_from_classes(get_classes(fill_el))

                    if left_off or right_off:
                        day_has_disconnections = True

                halves = [
                    HalfCell(
                        start=fmt_time(l_h, l_m),
                        end=fmt_time(l_e_h, l_e_m),
                        off=bool(left_off),
                        confirm=confirmed if left_off else None,
                    ),
                    HalfCell(
                        start=fmt_time(r_h, r_m),
                        end=fmt_time(r_e_h, r_e_m),
                        off=bool(right_off),
                        confirm=confirmed if right_off else None,
                    ),
                ]

            else:
                halves = [
                    HalfCell(
                        start=fmt_time(l_h, l_m),
                        end=fmt_time(l_e_h, l_e_m),
                        off=False,
                        confirm=None,
                    ),
                    HalfCell(
                        start=fmt_time(r_h, r_m),
                        end=fmt_time(r_e_h, r_e_m),
                        off=False,
                        confirm=None,
                    ),
                ]

            day_rows.append(
                HourCell(
                    hour=hour_str,
                    full=FullCell(
                        off=bool(full_off or (halves[0].off and halves[1].off)),
                        confirm=confirm_disconnection,
                    ),
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

    if not any(day.has_disconnections for day in disconnection_days):
        logger.info(
            f"No disconnections found for {address_name} for the next {max_days} days."
        )
        # If no disconnections are found, we can return early with an empty response.
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
