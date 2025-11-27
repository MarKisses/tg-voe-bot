import httpx
from config import settings


async def fetch(url: str, params: dict | None = None, data: dict | None = None, method: str = "GET"):
    headers = settings.fetcher.user_agent
    cookie = settings.fetcher.cookie
    base_url = settings.fetcher.base_url

    async with httpx.AsyncClient(base_url=base_url) as client:
        r = await client.request(
            method,
            url,
            headers=headers,
            params=params,
            cookies={"cf_clearance": cookie} if cookie else None,
            data=data,
            follow_redirects=True,
        )
        r.raise_for_status()
        return r.json()