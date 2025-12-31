import re
from datetime import date, datetime
from typing import List, Optional, Tuple


def _confirm_from_classes(classes: List[str]) -> Optional[bool]:
    if not classes:
        return None
    if "confirm_1" in classes:
        return True
    if "confirm_0" in classes:
        return False
    return None


def _has_disconnection(classes: List[str]) -> Optional[bool]:
    if not classes:
        return None

    return "has_disconnection" in classes


def _has_full_disconnection(classes: List[str]) -> Optional[bool]:
    if not classes:
        return None

    return all(
        (sep_class in classes for sep_class in ["has_disconnection", "full_hour"])
    )


def _safe_get_classes(el) -> List[str]:
    return el.get("class", []) if el else []


def _parse_css_var(style: str, name: str) -> float | None:
    m = re.search(rf"--{name}\s*:\s*([\d.]+)", style)
    return float(m.group(1)) if m else None


def _get_classes(el) -> list[str]:
    """
    Быстрая замена _safe_get_classes для lxml
    """
    if el is None:
        return []
    cls = el.get("class")
    return cls.split() if cls else []


def _inc_time(hour: int, minute: int, delta_minutes: int) -> Tuple[int, int]:
    total = hour * 60 + minute + delta_minutes
    total = total % (24 * 60)
    h = total // 60
    m = total % 60
    return h, m


def _fmt_time(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"


def _parse_day_label(label: str) -> date:
    today = datetime.now().date()

    _, data_label = label.split(" ")
    day, month = map(int, data_label.split("."))

    candidate_date = datetime(year=today.year, month=month, day=day).date()

    if candidate_date < today:
        candidate_date = datetime(year=today.year + 1, month=month, day=day).date()

    return candidate_date
