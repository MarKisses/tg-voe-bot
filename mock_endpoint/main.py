import json
import random
import logging

from aiohttp import web

PORT = 8888

routes = web.RouteTableDef()

logging.basicConfig(level=logging.DEBUG)


@routes.get("/disconnection/detailed/autocomplete/read_city")
async def get_city(request):
    q = request.rel_url.query.get("q", "")

    if not q:
        return web.json_response(
            status=404,
            data={"error": "Query parameter 'q' is required"},
        )

    with open("./responses_json/city.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        if not data:
            return web.json_response(status=500, data={"error": "No cities found"})
    city_to_send = random.choice(data)
    return web.json_response([city_to_send])


@routes.get("/disconnection/detailed/autocomplete/read_street/{city_id}")
async def get_street(request):
    city_id = request.match_info.get("city_id", "")
    q = request.rel_url.query.get("q", "")

    if not city_id or not q:
        return web.json_response(
            status=404,
            data={
                "error": "Path parameter city_id and query parameter 'q' is required"
            },
        )

    with open("./responses_json/street.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        if not data:
            return web.json_response(status=500, data={"error": "No streets found"})
    street_to_send = random.choice(data)
    return web.json_response([street_to_send])


@routes.get("/disconnection/detailed/autocomplete/read_house/{street_id}")
async def get_house(request):
    street_id = request.match_info.get("street_id", "")
    q = request.rel_url.query.get(
        "q", "Path parameter city_id and query parameter 'q' is required"
    )

    if not street_id or not q:
        return web.json_response(
            status=404,
            data={
                "error": "Path parameter city_id and query parameter 'q' is required"
            },
        )
    with open("./responses_json/house.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        if not data:
            return web.json_response(status=500, data={"error": "No houses found"})
    houses_to_send = random.choice(data)
    return web.json_response([houses_to_send])


@routes.post("/disconnection/detailed/")
async def get_schedule(request):
    params = {
        "search_type": request.rel_url.query.get("search_type"),
        "city_id": request.rel_url.query.get("city_id"),
        "street_id": request.rel_url.query.get("street_id"),
        "house_id": request.rel_url.query.get("house_id"),
        "ajax_form": request.rel_url.query.get("ajax_form"),
    }

    if not any(params.values()):
        return web.json_response(
            status=404,
            data={"error": "Check your query params!"},
        )


    empty_schedule = open(
        "./responses_json/graph_empty.json",
        "r",
        encoding="utf-8",
    )
    full_schedule = open(
        "./responses_json/graph_full.json",
        "r",
        encoding="utf-8",
    )

    # schedule_to_send = random.choice((json.load(full_schedule)))
    return web.json_response(json.load(full_schedule))


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=PORT)
