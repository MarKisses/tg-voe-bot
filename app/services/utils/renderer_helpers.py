from typing import Literal

from PIL import ImageDraw, ImageFont
from services.models import FullCell, HalfCell

COLOR_BG = (255, 255, 255)
COLOR_HEADER = (102, 111, 117) # #666F75 Dark gray
COLOR_GRID = (0, 0, 0)
COLOR_OFF = (245, 106, 105)  # #F56A69 Red
COLOR_POSSIBLE = (216, 214, 93)  # #D8D65D Slightly desaturated yellow
COLOR_OK = (230, 230, 230)  # gray


def half_color(h: HalfCell | FullCell):
    if h.off and h.confirm is True:
        return COLOR_OFF
    if h.off and h.confirm is False:
        return COLOR_POSSIBLE
    return COLOR_OK


class TextBox:
    def __init__(
        self,
        draw: ImageDraw.ImageDraw,
        xy_top_left: tuple[float, float],
        width: int,
        height: int,
        max_font_size: int = 32,
        min_font_size: int = 2,
        line_spacing: int = 4,
        align: Literal["center", "left", "right"] = "center",
        font_path: str = "app/services/utils/fonts/arial.ttf",
        valign: Literal["center", "top", "bottom"] = "center",
        fill: str = "black",
        padding_left: int = 0,
        padding_right: int = 0,
        padding_top: int = 0,
        padding_bottom: int = 0,
    ):
        self._draw = draw
        self.x, self.y = xy_top_left
        self.width = width
        self.height = height
        self.font_path = font_path
        self.max_font_size = max_font_size
        self.min_font_size = min_font_size
        self.line_spacing = line_spacing
        self.align = align
        self.valign = valign
        self.fill = fill

        # new:
        self.padding_left = padding_left
        self.padding_right = padding_right
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom

        # inner dimensions
        self.inner_width = width - padding_left - padding_right
        self.inner_height = height - padding_top - padding_bottom

    def draw_text(self, text: str):
        font_size = self.max_font_size
        total_h = 0
        lines = []
        heights = []
        font = None

        # Determine font size that fits in the box
        while font_size >= self.min_font_size:
            font = ImageFont.truetype(self.font_path, font_size)
            lines = self._wrap_text(text, font)
            total_h, max_w, heights = self._measure_lines(lines, font)

            if total_h <= self.inner_height:
                break

            font_size -= 1

        # If we exit the loop without finding a fitting size, use min_font_size
        if font_size < self.min_font_size:
            font = ImageFont.truetype(self.font_path, self.min_font_size)
            lines = self._wrap_text(text, font)
            total_h, max_w, heights = self._measure_lines(lines, font)

        # Vertical alignment
        if self.valign == "center":
            y = self.y + self.padding_top + (self.inner_height - total_h) / 2
        elif self.valign == "top":
            y = self.y + self.padding_top
        elif self.valign == "bottom":
            y = self.y + self.height - self.padding_bottom - total_h
        else:
            y = self.y + self.padding_top

        # Draw text lines
        for line, h in zip(lines, heights):
            w = self._draw.textlength(line, font)

            # Horizontal alignment
            if self.align == "center":
                x = self.x + self.padding_left + (self.inner_width - w) / 2
            elif self.align == "left":
                x = self.x + self.padding_left
            elif self.align == "right":
                x = self.x + self.width - self.padding_right - w
            else:
                x = self.x + self.padding_left

            self._draw.text((x, y), line, font=font, fill=self.fill)
            y += h + self.line_spacing

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont):
        lines = []
        for block in text.split("\n"):
            words = block.split()
            if not words:
                lines.append("")
                continue

            current = ""
            for w in words:
                test = (current + " " + w).strip()
                if self._draw.textlength(test, font) <= self.inner_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = w
            if current:
                lines.append(current)
        return lines

    def _measure_lines(self, lines: list[str], font: ImageFont.FreeTypeFont):
        heights = []
        widths = []

        for line in lines:
            bbox = self._draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            heights.append(h)
            widths.append(w)

        total_h = sum(heights) + self.line_spacing * (len(lines) - 1)
        max_w = max(widths) if widths else 0
        return total_h, max_w, heights
