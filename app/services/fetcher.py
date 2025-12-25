import json

import httpx
from bs4 import BeautifulSoup
from config import settings
from logger import create_logger

from .utils.fetch_wrapper import fetch

logger = create_logger(__name__)


async def fetch_cities(query: str | None):
    url = "/autocomplete/read_city"
    params = {"q": query}
    try:
        r = await fetch(url, params=params)
    except httpx.HTTPError as e:
        logger.error("Failed to fetch cities: %s", e)
        return []
    logger.info(r)

    if settings.flare.operating_mode == "proxy":
        soup = BeautifulSoup(r["solution"]["response"], "lxml")
        pre = soup.find("pre")
        if not pre:
            raise ValueError("No pre found in AJAX drupal response")
        return json.loads(pre.text)

    return r


async def fetch_streets(city_id: int | None, query: str | None):
    url = f"/autocomplete/read_street/{city_id}"
    params = {"q": query}
    try:
        r = await fetch(url, params=params)
    except httpx.HTTPError as e:
        logger.error("Failed to fetch streets: %s", e)
        return []

    if settings.flare.operating_mode == "proxy":
        soup = BeautifulSoup(r["solution"]["response"], "lxml")
        pre = soup.find("pre")
        if not pre:
            raise ValueError("No pre found in AJAX drupal response")
        return json.loads(pre.text)
    return r


async def fetch_houses(street_id: int | None, query: str | None):
    url = f"/autocomplete/read_house/{street_id}"
    params = {"q": query}
    try:
        r = await fetch(url, params=params)
    except httpx.HTTPError as e:
        logger.error("Failed to fetch houses: %s", e)
        return []
    if settings.flare.operating_mode == "proxy":
        soup = BeautifulSoup(r["solution"]["response"], "lxml")
        pre = soup.find("pre")
        if not pre:
            raise ValueError("No pre found in AJAX drupal response")
        return json.loads(pre.text)
    return r


async def fetch_schedule(city_id: int, street_id: int, house_id: int) -> str:
    # url = "/disconnection/detailed"
    url = ""

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
        return ""

    if settings.flare.operating_mode == "proxy":
        soup = BeautifulSoup(r["solution"]["response"], "lxml")
        textarea = soup.find("textarea")
        if not textarea:
            raise ValueError("No textarea found in AJAX drupal response")
        return json.loads(textarea.text)[3]["data"]

    value = next((item for item in r if item.get("command","") == "insert"))
    return value["data"]
