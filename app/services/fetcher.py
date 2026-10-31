import asyncio
import json
import re

import httpx
from bs4 import BeautifulSoup
from config import settings
from logger import create_logger
from exceptions import VoeDownException

from .utils.fetch_wrapper import fetch

logger = create_logger(__name__)


def _unwrap_json(r: dict) -> dict:
    """In proxy mode FlareSolverr returns JSON rendered by the browser inside <pre>."""
    if settings.flare.operating_mode != "proxy":
        return r

    soup = BeautifulSoup(r["solution"]["response"], "lxml")
    pre = soup.find("pre")
    if not pre:
        raise ValueError("No pre found in FlareSolverr response")
    return json.loads(pre.text)


def _unwrap_items(r: dict) -> list[dict]:
    data = _unwrap_json(r)
    if not data.get("ok"):
        logger.warning("Autocomplete returned not ok: %s", data)
        return []
    return data.get("items", [])


CSRF_RE = re.compile(r'name="csrf"\s+value="([^"]+)"')
CSRF_ERROR = "Помилка безпеки"

_csrf_token: str | None = None
_csrf_lock = asyncio.Lock()


async def _fetch_csrf_token() -> str:
    """
    Loads the search page to get csrf token.
    Token is bound to the site session (PHPSESSID): in cookie mode it is kept
    in fetch_wrapper, in proxy mode in the FlareSolverr session.
    """
    r = await fetch(settings.fetcher.page_url, as_text=True)
    html = r["solution"]["response"] if settings.flare.operating_mode == "proxy" else r

    match = CSRF_RE.search(html)
    if not match:
        raise ValueError("No csrf token found on the search page")
    return match.group(1)


async def _get_csrf_token(refresh: bool = False) -> str:
    global _csrf_token

    old_token = _csrf_token
    async with _csrf_lock:
        # Other coroutine could already refresh it while we were waiting
        if _csrf_token and (not refresh or _csrf_token != old_token):
            return _csrf_token

        logger.info("Fetching new csrf token...")
        _csrf_token = await _fetch_csrf_token()
        return _csrf_token


async def fetch_cities(query: str | None):
    url = "/autocomplete.php"
    params = {
        "type": "city",
        "q": query,
    }
    try:
        r = await fetch(url, params=params)
    except httpx.HTTPStatusError as e:
        logger.error("Failed to fetch cities: %s", e)
        if e.response.status_code >= 500:
            raise VoeDownException
        return []
    return _unwrap_items(r)


async def fetch_streets(city_id: int | None, query: str | None):
    url = "/autocomplete.php"
    params = {
        "type": "street",
        "q": query,
        "ref": city_id,
    }
    try:
        r = await fetch(url, params=params)
    except httpx.HTTPStatusError as e:
        logger.error("Failed to fetch streets: %s", e)
        if e.response.status_code >= 500:
            raise VoeDownException
        return []

    return _unwrap_items(r)


async def fetch_houses(street_id: int | None, query: str | None):
    url = "/autocomplete.php"
    params = {
        "type": "house",
        "q": query,
        "ref": street_id,
    }
    try:
        r = await fetch(url, params=params)
    except httpx.HTTPStatusError as e:
        logger.error("Failed to fetch houses: %s", e)
        if e.response.status_code >= 500:
            raise VoeDownException
        return []
    return _unwrap_items(r)


async def fetch_schedule(city_id: int, street_id: int, house_id: int) -> dict | None:
    url = "/search.php"

    # Browser sends multipart/form-data, but PHP reads urlencoded body into $_POST
    # the same way. Urlencoded is also the only format FlareSolverr postData supports.
    data = {
        "type": "address",
        "value": house_id,
        "city_id": city_id,
        "street_id": street_id,
        "house_id": house_id,
    }

    for attempt in range(2):
        try:
            data["csrf"] = await _get_csrf_token(refresh=attempt > 0)
            r = await fetch(url, data=data, method="POST")
        except httpx.HTTPStatusError as e:
            logger.error("Failed to fetch schedule: %s", e)
            if e.response.status_code >= 500:
                raise VoeDownException
            return None

        result = _unwrap_json(r)
        if result.get("ok"):
            return result

        if CSRF_ERROR in (result.get("message") or ""):
            logger.warning("Csrf token rejected, refreshing session...")
            continue

        logger.warning("Search returned not ok: %s", result)
        return None

    logger.error("Search failed after csrf refresh: %s", result)
    return None
