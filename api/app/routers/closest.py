""" some docstring """

import faulthandler

# import pandas as pd
import geopandas as gpd
import json

# import joblib as jbl
# from fastapi.responses import JSONResponse
from fastapi import APIRouter

# from enum import auto
from api.app import schemas

# from api.app.jhm_metric_calcs.jhm_metric import main

# from app.routers_utils import validate_company_location, validate_workers_salary
from api.app.utils.data_reader import (
    # ontology,
    # grads,
    cities,
    # cv,
    # model,
)

from api.app.methods.methods_get_closest.select_closest_cities import find_n_closest_cities
from api.app.methods.methods_get_closest.route_api_caller import get_route

import shapely

router = APIRouter()
faulthandler.enable()


@router.get("/")
async def read_root():
    """some docstring"""
    return {"Hello": "World"}


@router.post("/plant/get_closest_cities", response_model=dict)
def get_closest_cities(query_params: schemas.ClosestCitiesQueryParamsRequest):

    # worker_and_count = query_params.worker_and_count
    # industry_name = query_params.industry_name

    point = query_params.company_location
    point = shapely.geometry.Point(point["lon"], point["lng"])
    hour_radius = query_params.n_hours

    closest_cities = find_n_closest_cities(
        point=point, gdf_cities=cities, search_radius_in_h=hour_radius
    )

    get_routes = lambda city: get_route(
        start_coords=(point.x, point.y), end_coords=(city.x, city.y)
    )

    data = list(map(get_routes, closest_cities["geometry"]))

    # # Создание GeoDataFrame
    routes = gpd.GeoDataFrame(data, geometry="geometry")

    # # Установка CRS, если необходимо
    routes.set_crs(epsg=4326, inplace=True)
    closest_cities.loc[:, "hours"] = routes["duration"].values

    return {
        "estimates": json.loads(closest_cities.to_json()),
        "links": json.loads(routes.to_json()),
        # "links": result["links"],
    }
