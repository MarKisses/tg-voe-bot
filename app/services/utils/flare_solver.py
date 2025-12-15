from urllib.parse import urlencode

import httpx
from config import settings
from logger import create_logger

FLARE_URL = settings.flare.url
logger = create_logger(__name__)


async def solve_challenge(target_url: str):
    """
    Просит FlareSolverr пройти challenge на target_url.
    Возвращает dict: {"cookies": [...], "userAgent": "..."}
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "cmd": "request.get",
        "url": target_url,
        "maxTimeout": 120000,
        "returnOnlyCookies": True,
        "disableMedia": True,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(FLARE_URL, json=payload, headers=headers)
        r.raise_for_status()
        res = r.json()

    if res.get("status") != "ok":
        raise RuntimeError("FlareSolverr failed: " + str(res))

    solution = res["solution"]
    return {
        "cookies": solution.get("cookies", []),
        "user_agent": solution.get("userAgent"),
    }


async def flare_proxy(
    target_url: str,
    params: dict | None = None,
    data: dict | None = None,
    method: str = "GET",
):
    headers = {"Content-Type": "application/json"}

    if params:
        target_url = f"{target_url}?{urlencode(params)}"

    payload = {
        "cmd": f"request.{method.lower()}",
        "url": target_url,
        "session": settings.flare.session,
        "maxTimeout": 120000,
    }

    if method.lower() != "get" and data:
        payload["postData"] = urlencode(data)

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(FLARE_URL, json=payload, headers=headers)
        r.raise_for_status()
        res = r.json()

    return res
