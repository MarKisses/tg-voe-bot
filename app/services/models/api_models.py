"""Raw response models of disconnection.voe.com.ua/api/search.php"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class ApiSegment(ApiModel):
    # Type is css class of the segment, e.g. "confirm_1"
    type: str = ""
    # Start and size are percents of the hour
    start: float = 0
    size: float = 0
    label: str = ""


class ApiCell(ApiModel):
    hour: str
    segments: list[ApiSegment] = []
    class_: str = Field("", alias="class")


class ApiRow(ApiModel):
    date: date
    label: str = ""
    class_: str = Field("", alias="class")
    cells: list[ApiCell] = []


class ApiMessage(ApiModel):
    # 1 - warning, 2 - error (disconnection), 3 - ok
    type: int | None = None
    title: str | None = None
    text: str | None = None
    queue: str | int | float | None = None
    from_: str | None = Field(None, alias="from")
    to: str | None = None


class ApiTable(ApiModel):
    listnum: str | int | float | None = None
    header: list[str] = []
    rows: list[ApiRow] = []
    message: ApiMessage | None = None
    reserve: int | bool = 0
    empty: bool = False


class ApiSearchResponse(ApiModel):
    ok: bool
    type: str | None = None
    # dict {eic: label} when several addresses found, otherwise empty list
    addresses: dict[str, str] | list = []
    tables: list[ApiTable] = []
    message: str | None = None
