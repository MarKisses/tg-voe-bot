import asyncio
from asyncio import Semaphore

import httpx
from config import settings
from logger import create_logger

from .flare_solver import flare_proxy, solve_challenge

logger = create_logger(__name__)

RETRY_STATUSES = {500, 502, 503, 504}
MAX_RETRIES = 4
BASE_DELAY = 1.0


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
http_sem = Semaphore(3)


async def fetch(
    url: str, params: dict | None = None, data: dict | None = None, method: str = "GET"
):
    async with http_sem:
        base_url = settings.fetcher.base_url

        if settings.flare.operating_mode == "proxy":
            return await flare_proxy(
                f"{base_url}{url}",
                params=params,
                data=data,
                method=method,
            )

        async with httpx.AsyncClient(base_url=base_url, timeout=150) as client:
            attempt = 0

            while True:
                cookie = settings.fetcher.cookie
                headers = settings.fetcher.headers
                cookies = {"cf_clearance": cookie} if cookie else None

                try:
                    r = await _attempt_request(
                        client, method, url, headers, params, cookies, data
                    )
                    # r.raise_for_status()
                    if r.status_code == 403:
                        logger.info(
                            "🔥 Cloudflare challenge detected, using FlareSolverr…"
                        )

                        full_url = f"{base_url}{url}"
                        solution = await solve_challenge(full_url)

                        for c in solution["cookies"]:
                            if c["name"] == "cf_clearance":
                                settings.fetcher.cookie = c["value"]

                        if solution["user_agent"]:
                            settings.fetcher.user_agent = {
                                "User-Agent": solution["user_agent"]
                            }
                        continue

                    if r.status_code in RETRY_STATUSES:
                        raise httpx.HTTPStatusError(
                            "Server error, retrying...", request=r.request, response=r
                        )
                    r.raise_for_status()
                    return r.json()

                except (httpx.TimeoutException, httpx.NetworkError):
                    err = "network"

                except httpx.HTTPStatusError as e:
                    if e.response.status_code not in RETRY_STATUSES:
                        raise
                    err = f"HTTP {e.response.status_code}"

                attempt += 1
                if attempt > MAX_RETRIES:
                    logger.error(f"❌ {url} failed after {MAX_RETRIES} retries ({err})")
                    raise

                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    f"Retry {attempt}/{MAX_RETRIES} after {err}, sleeping {delay:.1f}s"
                )
                await asyncio.sleep(delay)
