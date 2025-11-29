import httpx
import logging
from .utils.fetch_wrapper import fetch

logger = logging.getLogger(__name__)


async def fetch_cities(query: str | None):
    url = "/autocomplete/read_city"
    params = {"q": query}
    try:
        r = await fetch(url, params=params)
    except httpx.HTTPError as e:
        logger.error("Failed to fetch cities: %s", e)
        return []
    return r


async def fetch_streets(city_id: int | None, query: str | None):
    url = f"/autocomplete/read_street/{city_id}"
    params = {"q": query}
    try:
        r = await fetch(url, params=params)
    except httpx.HTTPError as e:
        logger.error("Failed to fetch streets: %s", e)
        return []
    return r


async def fetch_houses(street_id: int | None, query: str | None):
    url = f"/autocomplete/read_house/{street_id}"
    params = {"q": query}
    try:
        r = await fetch(url, params=params)
    except httpx.HTTPError as e:
        logger.error("Failed to fetch houses: %s", e)
        return []
    return r


async def fetch_schedule(city_id: int, street_id: int, house_id: int):
    url = "/disconnection/detailed"

    params = {
        "search_type": 0,
        "city_id": city_id,
        "street_id": street_id,
        "house_id": house_id,
        "ajax_form": 1,
    }
    data = {
        "search_type": 0,
        "city_id": city_id,
        "street_id": street_id,
        "house_id": house_id,
        "form_id": "disconnection_detailed_search_form",
    }

    try:
        r = await fetch(url, params=params, data=data, method="POST")
    except httpx.HTTPError as e:
        logger.error("Failed to fetch schedule: %s", e)
        return []
    
    with open("debug_schedule_response.json", "w", encoding="utf-8") as f:
        f.write(str(r))

    return r[3]["data"]
