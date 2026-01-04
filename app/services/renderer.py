from io import BytesIO

from PIL import Image, ImageDraw

from services.models import DaySchedule

from .utils.renderer_helpers import (
    TextBox,
    half_color,
)

from config import settings


def render_schedule_image(
    day: DaySchedule, queue: str, date: str, address: str
) -> BytesIO:
    IMAGE_W = 1000
    IMAGE_H = 1000
    cols = 4
    rows = 6

    col_w = IMAGE_W // (cols + 1)  # +1 col for side paddings
    row_h = IMAGE_H // (rows + 4)  # +4 rows for upper and bottom paddings

    img = Image.new("RGBA", (IMAGE_W, IMAGE_H), settings.renderer.color_bg)
    draw = ImageDraw.Draw(img)

    # ---- Заголовок ----
    header_text = f"{queue} | {date} | {address}"
    draw.rectangle(
        [col_w / 2, row_h / 2, IMAGE_W - (col_w / 2), row_h / 2 + row_h],
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
        max_font_size=int(IMAGE_W * 0.04),
        fill="white",
        padding_left=10,
        padding_top=10,
        padding_bottom=10,
        padding_right=10,
    ).draw_text(header_text)

    # ---- Таблица ----
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

        if full.off is True:
            # confirmed full hour
            color = half_color(full)
            draw.rectangle([x1, y1, x2, y2], fill=color)
            if full.confirm:
                cell_text_fill = "white"
                
        else:
            # left half
            h1 = halves[0]
            h1_color = half_color(h1)
            draw.rectangle([x1, y1, x2 - col_w / 2, y2], fill=h1_color)

            # right half
            h2 = halves[1]
            h2_color = half_color(h2)
            draw.rectangle([x1 + col_w / 2, y1, x2, y2], fill=h2_color)

        cell_text = TextBox(
            draw, (x1, y1), col_w, row_h, max_font_size=int(IMAGE_W * 0.035), fill=cell_text_fill
        )
        cell_text.draw_text(hour)

    for c in range(cols + 1):
        x = col_w / 2 + c * col_w
        draw.line((x, row_h * 2, x, row_h * 2 + rows * row_h), fill=settings.renderer.color_grid, width=4)

    for r in range(rows + 1):
        y = row_h * 2 + r * row_h
        draw.line((col_w / 2, y, col_w / 2 + cols * col_w, y), fill=settings.renderer.color_grid, width=4)

    # ---- Легенда ----

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
        max_font_size=int(IMAGE_W * 0.036),
        padding_right=50,
    ).draw_text("Можливе відключення")

    TextBox(
        draw,
        (col_w * 3.5, row_h * 8.5),
        col_w,
        row_h,
        max_font_size=int(IMAGE_W * 0.036),
        padding_right=50,
    ).draw_text("Підтверджене\nвідключення")

    # ---- Сохранение в память ----
    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output
