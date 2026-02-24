from datetime import datetime
from io import BytesIO
from typing import Callable

from config import settings
from logger import create_logger
from PIL import Image, ImageDraw
from services.models import (
    CurrentDisconnection,
    DaySchedule,
    HalfCell,
    ImageResult,
    RenderedSchedule,
    TextResult,
)

from .utils.renderer_helpers import (
    TextBox,
    half_color,
)

logger = create_logger(__name__)


def render_schedule_image(
    day: DaySchedule,
    current_disconnection: CurrentDisconnection | None,
    queue: str,
    date: datetime,
    address: str,
) -> bytes:
    """
    Render schedule as an image and return it as bytes.
    """
    date_str = date.strftime("%d-%m-%Y")

    image_w = 1000
    image_h = 1000
    cols = 4
    rows = 6

    col_w = image_w // (cols + 1)  # +1 col for side padsdings
    row_h = image_h // (rows + 4)  # +4 rows for upper and bottom paddings

    img = Image.new("RGBA", (image_w, image_h), settings.renderer.color_bg)
    draw = ImageDraw.Draw(img)

    header_text = f"{queue} | {date_str} | {address}"
    draw.rectangle(
        [col_w / 2, row_h / 2, image_w - (col_w / 2), row_h / 2 + row_h],
        fill=settings.renderer.color_header,
        outline=settings.renderer.color_grid,
        width=4,
    )

    TextBox(
        draw,
        (col_w / 2, row_h * 0.5),
        col_w * 4,
        row_h,
        min_font_size=3,
        max_font_size=int(image_w * 0.04),
        fill="white",
        padding_left=10,
        padding_top=10,
        padding_bottom=10,
        padding_right=10,
    ).draw_text(header_text)

    hours_list = day.cells

    for i, hour_obj in enumerate(hours_list):
        hour = hour_obj.hour
        full = hour_obj.full
        halves = hour_obj.halves
        cell_text_fill = "black"

        r = i // cols
        c = i % cols

        x1 = col_w / 2 + c * col_w
        y1 = row_h * 2 + r * row_h
        x2 = x1 + col_w
        y2 = y1 + row_h

        cell_text = TextBox(
            draw,
            (x1, y1),
            col_w,
            row_h,
            max_font_size=int(image_w * 0.035),
        )

        if full.off:
            # confirmed full hour
            color = half_color(full)
            draw.rectangle([x1, y1, x2, y2], fill=color)
            if full.confirm:
                cell_text.fill = "white" if full.confirm else "black"
                cell_text.draw_text(hour)
        else:
            h1 = halves[0]
            h2 = halves[1]

            h1_color = half_color(h1)
            h2_color = half_color(h2)

            draw.rectangle([x1, y1, x2 - col_w / 2, y2], fill=h1_color)
            draw.rectangle([x1 + col_w / 2, y1, x2, y2], fill=h2_color)

            mask = cell_text.render_text_mask(hour)

            text_layer = Image.new(
                "RGBA",
                (int(col_w), int(row_h)),
                (0, 0, 0, 0),
            )

            left_color = "white" if h1.confirm else "black"
            right_color = "white" if h2.confirm else "black"

            left_part = Image.new(
                "RGBA",
                (int(col_w / 2), int(row_h)),
                left_color,
            )
            right_part = Image.new(
                "RGBA",
                (int(col_w / 2), int(row_h)),
                right_color,
            )
            
            text_layer.paste(left_part, (0, 0))
            text_layer.paste(right_part, (int(col_w / 2), 0))

            img.paste(text_layer, (int(x1), int(y1)), mask)

    for c in range(cols + 1):
        x = col_w / 2 + c * col_w
        draw.line(
            (x, row_h * 2, x, row_h * 2 + rows * row_h),
            fill=settings.renderer.color_grid,
            width=4,
        )

    for r in range(rows + 1):
        y = row_h * 2 + r * row_h
        draw.line(
            (col_w / 2, y, col_w / 2 + cols * col_w, y),
            fill=settings.renderer.color_grid,
            width=4,
        )

    draw.rounded_rectangle(
        [col_w * 0.5, row_h * 8.5, col_w * 1.1, row_h * 9.5],
        radius=20,
        fill=settings.renderer.color_possible,
        outline=settings.renderer.color_grid,
        width=2,
    )

    draw.rounded_rectangle(
        [col_w * 2.5, row_h * 8.5, col_w * 3.1, row_h * 9.5],
        radius=20,
        fill=settings.renderer.color_off,
        outline=settings.renderer.color_grid,
        width=2,
    )

    TextBox(
        draw,
        (col_w * 1.5, row_h * 8.5),
        col_w,
        row_h,
        max_font_size=int(image_w * 0.036),
        padding_right=50,
    ).draw_text("Можливе відключення")

    TextBox(
        draw,
        (col_w * 3.5, row_h * 8.5),
        col_w,
        row_h,
        max_font_size=int(image_w * 0.036),
        padding_right=50,
    ).draw_text("Підтверджене\nвідключення")

    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output.getvalue()


def consume_range(
    halves: list[HalfCell],
    start_index: int,
    predicate: Callable,
) -> tuple[int, str | None, float]:
    length = len(halves)
    i = start_index

    if i >= length or not predicate(halves[i]):
        return i, None, 0

    start = halves[i].start
    hours = 0

    while i < length and predicate(halves[i]):
        hours += 0.5
        i += 1

    end = halves[i - 1].end
    return i, f"{start} - {end}", hours


def hour_str_modifier(disconnection_length: float) -> str:
    def format_hour_word(hours: float) -> str:
        return str(int(hours) if hours.is_integer() else hours)

    hours = disconnection_length
    hours_int = int(hours)

    last_two = hours_int % 100
    last_one = hours_int % 10

    if 11 <= last_two <= 14:
        word = "годин"
    elif last_one == 1:
        word = "година"
    elif 2 <= last_one <= 4:
        word = "години"
    else:
        word = "годин"

    return f"<b>{format_hour_word(hours)} {word}</b>"


def generate_disconnection_message(
    current_disconnection: CurrentDisconnection | None,
) -> str:
    if not current_disconnection:
        return ""
    if current_disconnection and current_disconnection.has_disconnection:
        start_time = "Невідомо"
        end_time = "Невідомо"
        if current_disconnection.started_at and current_disconnection.estimated_end:
            start_time = current_disconnection.started_at.strftime("%H:%M %d-%m-%Y")
            end_time = current_disconnection.estimated_end.strftime("%H:%M %d-%m-%Y")

        return (
            "За вашою адресою зараз відсутня електроенергія.\n"
            f"Причина: <b><u>{current_disconnection.reason or 'Невідома'}</u></b>.\n"
            f"Час початку: <b>{start_time}</b>.\n"
            f"Орієнтовний час відновлення: <b>{end_time}</b>.\n"
        )
    return ""


def render_schedule_text(
    day: DaySchedule,
    current_disconnection: CurrentDisconnection | None,
    queue: str,
    date: datetime,
    address: str,
) -> str:
    """
    Render schedule text for Telegram message.
    """
    disconnection_date_str = date.strftime("%d-%m-%Y")

    lines: list[str | None] = [
        f"<b>{queue}</b> · <b>{disconnection_date_str}</b>\n",
        f"📍 {address}\n",
    ]

    current_disconnection_part = generate_disconnection_message(current_disconnection)
    if current_disconnection_part:
        lines.append(current_disconnection_part)

    halves = [halve for hour in day.cells for halve in hour.halves]

    confirmed = 0
    unconfirmed = 0

    i = 0
    while i < len(halves):
        # Confirmed disconnections
        i, range_str, hours = consume_range(halves, i, lambda h: h.off and h.confirm)
        if range_str:
            confirmed += hours
            lines.append(f"🟥 <b>{range_str}</b> — Підтверджене відключення")

        # Unconfirmed disconnections
        i, range_str, hours = consume_range(
            halves, i, lambda h: h.off and not h.confirm
        )
        if range_str:
            unconfirmed += hours
            lines.append(f"🟧 <b>{range_str}</b> — Можливе відключення")

        # No disconnection
        i, range_str, hours = consume_range(halves, i, lambda h: not h.off)
        if range_str:
            lines.append(f"🟩 <b>{range_str}</b> — Зі світлом")
        lines.append(" ")

    lines.extend(
        [
            f"Підтверджених відключень: {hour_str_modifier(confirmed)}",
            f"Можливих відключень: {hour_str_modifier(unconfirmed)}"
            if unconfirmed
            else None,
            f"Зі світлом: {hour_str_modifier(24 - confirmed - unconfirmed)}",
            f"Оновлено: <b>{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</b>",
        ]
    )

    return "\n".join(filter(None, lines))


def render_schedule(
    day: DaySchedule,
    is_text_enabled: bool,
    queue: str,
    date: datetime,
    address: str,
    current_disconnection: CurrentDisconnection | None = None,
) -> RenderedSchedule:
    if is_text_enabled:
        return TextResult(
            text=render_schedule_text(
                day,
                current_disconnection,
                queue,
                date,
                address,
            )
        )
    else:
        return ImageResult(
            text=generate_disconnection_message(current_disconnection),
            image_bytes=render_schedule_image(
                day,
                current_disconnection,
                queue,
                date,
                address,
            ),
        )
