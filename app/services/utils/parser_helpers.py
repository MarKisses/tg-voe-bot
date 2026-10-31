from datetime import datetime
from typing import List, Optional, Tuple

from logger import create_logger
from services.models import CurrentDisconnection
from services.models.api_models import ApiMessage, ApiSegment

logger = create_logger(__name__)

DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d.%m.%Y %H:%M",
    "%H:%M %d.%m.%Y",
    "%H:%M %Y.%m.%d",
)

# message.type from api: 1 - warning, 2 - error, 3 - ok
MESSAGE_TYPE_DISCONNECTION = 2


# Segment classes from the site css:
#   confirm_0 - transparent, no disconnection
#   confirm_1 - not used anymore (commented out in css)
#   confirm_2 - "Заплановано", planned
#   confirm_3 - "Застосовано", applied
#   confirm_4 - "Завершено", finished
NO_DISCONNECTION_CLASS = "confirm_0"


def confirm_from_classes(classes: List[str]) -> Optional[bool]:
    if not classes:
        return None
    if "confirmed" in classes:
        return True
    if "confirm_0" in classes:
        return False
    if "confirm_1" in classes:
        return True
    if "confirm_2" in classes:
        return False
    if "confirm_3" in classes:
        return True
    if "confirm_4" in classes:
        return True
    return None


def segment_is_off(segment: ApiSegment) -> bool:
    return NO_DISCONNECTION_CLASS not in segment.type.split()


def segment_confirm(segment: ApiSegment) -> Optional[bool]:
    confirm = confirm_from_classes(segment.type.split())
    if confirm is None:
        logger.warning(
            f"Unknown segment type '{segment.type}' (label: '{segment.label}')"
        )
    return confirm


def segment_minutes(segment: ApiSegment) -> Tuple[int, int]:
    """Converts segment percents of the hour to (start_min, end_min)."""
    start_min = max(0, int(segment.start * 60 / 100))
    end_min = min(60, int((segment.start + segment.size) * 60 / 100))
    return start_min, end_min


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return b_start < a_end and b_end > a_start


def inc_time(hour: int, minute: int, delta_minutes: int) -> Tuple[int, int]:
    total = hour * 60 + minute + delta_minutes
    total = total % (24 * 60)
    h = total // 60
    m = total % 60
    return h, m


def fmt_time(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    logger.warning(f"Can't parse datetime '{value}'")
    return None


def current_disconnection_info(message: ApiMessage | None) -> CurrentDisconnection:
    if not message or message.type != MESSAGE_TYPE_DISCONNECTION:
        return CurrentDisconnection(
            has_disconnection=False,
            is_emergency=None,
            reason=None,
            started_at=None,
            estimated_end=None,
        )

    # Format of the active disconnection message is not confirmed yet
    logger.info(f"Active disconnection message: {message.model_dump()}")

    raw_text = f"{message.title or ''} {message.text or ''}".lower()

    return CurrentDisconnection(
        has_disconnection=True,
        is_emergency="аварій" in raw_text,
        reason=message.title,
        started_at=parse_dt(message.from_),
        estimated_end=parse_dt(message.to),
    )
