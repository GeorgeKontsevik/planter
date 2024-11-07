""" some docstring """

import faulthandler

# import pandas as pd
import geopandas as gpd
import h3
import json

# import joblib as jbl
# from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends

# from enum import auto
from api.app import enums, schemas

# from api.app.jhm_metric_calcs.jhm_metric import main

# from app.routers_utils import validate_company_location, validate_workers_salary
from api.app.data_reader import (
    # ontology,
    # grads,
    cities,
    # cv,
    # model,
)

from api.app.methods_get_closest.select_closest_cities import find_n_closest_cities
from api.app.methods_get_closest.route_api_caller import get_route
from api.app.constants import H3_RESOLUTION

import shapely

router = APIRouter()
faulthandler.enable()


# Define a function to convert lat/lon to H3 index at a specific resolution
# def _point_to_h3(point, resolution=8):
#     return h3.geo_to_h3(point.y, point.x, resolution)


@router.get("/")
async def read_root():
    """some docstring"""
    return {"Hello": "World"}


@router.post("/plant/get_closest_cities", response_model=dict)
def get_closest_cities(query_params: schemas.ClosestCitiesQueryParams):

    # worker_and_count = query_params.worker_and_count
    # industry_name = query_params.industry_name

    point = query_params.company_location
    point = shapely.geometry.Point(point["lat"], point["lon"])
    hour_radius = query_params.n_hours

    closest_cities = find_n_closest_cities(
        point=point, gdf_cities=cities, search_radius_in_h=hour_radius
    )

    get_routes = lambda city: get_route(
        start_coords=(point.x, point.y), end_coords=(city.x, city.y)
    )

    data = list(map(get_routes, closest_cities["geometry"]))

    # # Создание GeoDataFrame
    routes = gpd.GeoDataFrame(data)

    # # Установка CRS, если необходимо
    routes.set_crs(epsg=4326, inplace=True)
    # display(gdf)
    closest_cities.loc[:, "hours"] = routes["duration"].values
    # # Convert all city points to H3 indices
    # # test_point = Point(38.902091, 45.128569)  # (lon, lat)
    # cities["h3_index"] = cities.geometry.apply(lambda x: _point_to_h3(x, H3_RESOLUTION))
    # closest_cities = find_n_closest_cities(test_point, cities, n_hours, resolution)
    # # display(closest_cities)
    # # map_result = explore_closest_cities(test_point, closest_cities)

    return {
        "estimates": json.loads(closest_cities.to_json()),
        "links": json.loads(routes.to_json()),
        # "links": result["links"],
    }


# @router.post(
#     "/plant/estimates", response_model=schemas.EstimatesOut, tags=[Tags.estimates]
# )
# def get_potential_estimates(query_params: schemas.EstimatesIn):
#     result =

#     # result["estimates"].to_parquet('result_estimates.parquet')
#     return {
#         "estimates": result["estimates"].__geo_interface__,
#         "links": result["links"].__geo_interface__,
#     }
