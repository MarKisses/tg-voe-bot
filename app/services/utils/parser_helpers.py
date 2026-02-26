import re
from datetime import date, datetime
from typing import List, Optional, Tuple

from logger import create_logger
from services.models import CurrentDisconnection

logger = create_logger(__name__)


def confirm_from_classes(classes: List[str]) -> Optional[bool]:
    if not classes:
        return None
    if "confirmed" in classes:
        return True
    if "confirm_0" in classes:
        return False
    if "confirm_1" in classes:
        return False
    if "confirm_2" in classes:
        return False
    if "confirm_3" in classes:
        return True
    if "confirm_4" in classes:
        return True
    return None


def has_disconnection(classes: List[str]) -> Optional[bool]:
    if not classes:
        return None

    return "has_disconnection" in classes


def has_full_disconnection(classes: List[str]) -> Optional[bool]:
    if not classes:
        return None

    return all(
        (sep_class in classes for sep_class in ["has_disconnection", "full_hour"])
    )


def parse_css_var(style: str, name: str) -> float | None:
    m = re.search(rf"--{name}\s*:\s*([\d.]+)", style)
    return float(m.group(1)) if m else None


def get_classes(el) -> list[str]:
    """
    Get list of classes from an element.
    """
    if el is None:
        return []
    cls = el.get("class")
    return cls.split() if cls else []


def inc_time(hour: int, minute: int, delta_minutes: int) -> Tuple[int, int]:
    total = hour * 60 + minute + delta_minutes
    total = total % (24 * 60)
    h = total // 60
    m = total % 60
    return h, m


def fmt_time(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"


def parse_day_label(label: str) -> datetime:
    today = datetime.now()

    _, data_label = label.split(" ")
    day, month = map(int, data_label.split("."))

    candidate_date = datetime(year=today.year, month=month, day=day)

    if candidate_date.date() < today.date():
        candidate_date = datetime(year=today.year + 1, month=month, day=day)

    return candidate_date


def parse_dt(label: str, text: str) -> datetime | None:
    if label not in text:
        logger.debug(f"Label '{label}' not found in text for datetime parsing.")
        logger.debug(f"Text content: {text}")
        return None
    part = text.split(label, 1)[1].strip().split(" ")
    logger.debug(f"Parsing datetime part: {part}")
    try:
        return datetime.strptime(" ".join(part[:2]), "%H:%M %Y.%m.%d")
    except ValueError:
        return None


def current_disconnection_info(status_nodes: list[str]) -> CurrentDisconnection:
    raw_status = " ".join(status_nodes).strip()

    has_current_disconnection = "відсутня електроенергія" in raw_status
    if not has_current_disconnection:
        return CurrentDisconnection(
            has_disconnection=False,
            is_emergency=None,
            reason=None,
            started_at=None,
            estimated_end=None,
        )

    is_emergency = None
    reason = None
    started_at = parse_dt("Час початку – ", raw_status)
    estimated_end = None

    if "Причина відключення" in raw_status:
        if "Аварійне" in raw_status:
            is_emergency = True
            reason = "Аварійне відключення"
            estimated_end = parse_dt("Орієнтовний час завершення – до", raw_status)
        else:
            is_emergency = False
            reason = (
                raw_status.split("Причина відключення: ")[-1].split("Час")[0].strip()
            )
            estimated_end = parse_dt("Орієнтовний час відновлення – до", raw_status)

    return CurrentDisconnection(
        has_disconnection=True,
        is_emergency=is_emergency,
        reason=reason,
        started_at=started_at.isoformat() if started_at else None,
        estimated_end=estimated_end.isoformat() if estimated_end else None,
    )
