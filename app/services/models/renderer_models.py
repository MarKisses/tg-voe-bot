from typing import Union

from pydantic import BaseModel


class TextResult(BaseModel):
    text: str


class ImageResult(BaseModel):
    text: str | None = None
    image_bytes: bytes


RenderedSchedule = Union[TextResult, ImageResult]
