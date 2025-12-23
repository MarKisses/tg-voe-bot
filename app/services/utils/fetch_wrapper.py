import httpx
from config import settings
from asyncio import Semaphore
from .flare_solver import solve_challenge, flare_proxy

from logger import create_logger
logger = create_logger(__name__)

async def _attempt_request(
    client: httpx.AsyncClient, method, url, headers, params, cookies, data
):
    return await client.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        cookies=cookies,
        data=data,
        follow_redirects=True,
    )

# Limit concurrent HTTP requests
http_sem = Semaphore(1)

async def fetch(
    url: str, params: dict | None = None, data: dict | None = None, method: str = "GET"
):
    async with http_sem:
        base_url = settings.fetcher.base_url
        headers = settings.fetcher.headers
        cookie = settings.fetcher.cookie

        cookies = {"cf_clearance": cookie} if cookie else None
    
        if settings.flare.operating_mode == "proxy":
            return await flare_proxy(
                f"{base_url}{url}",
                params=params,
                data=data,
                method=method,
            )

        async with httpx.AsyncClient(base_url=base_url, timeout=150) as client:
            try:
                r = await _attempt_request(
                    client, method, url, headers, params, cookies, data
                )
                r.raise_for_status()
                return r.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code != 403:
                    raise

                logger.info("🔥 Cloudflare challenge detected, using FlareSolverr…")

                full_url = f"{base_url}{url}"
                solution = await solve_challenge(full_url)

                for c in solution["cookies"]:
                    if c["name"] == "cf_clearance":
                        settings.fetcher.cookie = c["value"]

                if solution["user_agent"]:
                    settings.fetcher.user_agent = {"User-Agent": solution["user_agent"]}

                new_headers = settings.fetcher.headers
                new_cookies = {"cf_clearance": settings.fetcher.cookie}

                r2 = await _attempt_request(
                    client, method, url, new_headers, params, new_cookies, data
                )
                r2.raise_for_status()
                return r2.json()
