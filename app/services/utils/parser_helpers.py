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


def _safe_get_classes(el) -> List[str]:
    return el.get("class", []) if el else []


def _inc_time(hour: int, minute: int, delta_minutes: int) -> Tuple[int, int]:
    total = hour * 60 + minute + delta_minutes
    total = total % (24 * 60)
    h = total // 60
    m = total % 60
    return h, m


def _fmt_time(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"
