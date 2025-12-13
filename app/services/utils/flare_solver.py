import httpx
from config import settings

FLARE_URL = settings.flare.url

async def solve_challenge(target_url: str):
    """
    Просит FlareSolverr пройти challenge на target_url.
    Возвращает dict: {"cookies": [...], "userAgent": "..."}
    """
    headers = {"Content-Type": "application/json"}
    payload = {"cmd": "request.get", "url": target_url, "maxTimeout": 120000}

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