import faulthandler
import geopandas as gpd
import json
import shapely.geometry

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
import pandas as pd

from api.app.utils.data_reader import cities
from api.app.methods.methods_get_closest.select_closest_cities import find_n_closest_cities
from api.app.methods.methods_estimate.estimator import closest_city_params
from api.app.methods.methods_get_closest.route_api_caller import get_route
from api.app import schemas

# from api.app.methods.methods_estimate.estimator import 

faulthandler.enable()

router = APIRouter()

cities = gpd.read_parquet(
    "api/app/data/cities.parquet"
)

ontology = pd.read_pickle("api/app/data/new_ontology.pkl")

grouped_grads = pd.read_pickle("api/app/data/grouped_grads.pkl")



# Define schemas for response models
class CityEstimate(BaseModel):
    id: int
    name: str
    hours: float
    geometry: dict  # GeoJSON-like structure


class Link(BaseModel):
    duration: float
    distance: float
    geometry: dict  # GeoJSON-like structure


@router.post(
    "/plant/get_closest_cities",
    summary="Get Closest Cities",
    description="Find closest cities within a given time radius and retrieve travel routes.",
)
def get_closest_cities(query_params: schemas.ClosestCitiesQueryParamsRequest):
    """
    Endpoint to retrieve closest cities and their travel routes based on the provided query parameters.
    """
    point_data = query_params.company_location
    point = shapely.geometry.Point(point_data["lon"], point_data["lng"])
    hour_radius = query_params.n_hours

    # Find closest cities
    try:
        closest_cities = find_n_closest_cities(
            point=point, gdf_cities=cities, search_radius_in_h=hour_radius
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error finding closest cities: {e}")

    # Get routes for closest cities
    try:
        get_routes = lambda city: get_route(
            start_coords=(point.x, point.y), end_coords=(city.x, city.y)
        )
        route_data = list(map(get_routes, closest_cities["geometry"]))
        routes = gpd.GeoDataFrame(route_data, geometry="geometry")
        routes.set_crs(epsg=4326, inplace=True)
        closest_cities.loc[:, "hours"] = routes["duration"].values
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching route data: {e}")

    # Prepare the response
    response = {
        "estimates": json.loads(closest_cities.to_json()),
        "links": json.loads(routes.to_json()),
    }
    return response


# Example router for competitor analysis
@router.post("/closest_city_params")
def competitor_analysis(
    uinput_spec_num: dict,
    uinput_industry: str,
    workforce_type: str,
    # ontology: dict,  # Convert this to a DataFrame before passing to the function
    # cities: dict,  # Convert this to a DataFrame before passing to the function
    # grouped_grads: dict,  # Convert this to a DataFrame before passing to the function
):
    try:
        ontology_df = pd.DataFrame(ontology)
        cities_df = pd.DataFrame(cities)
        grouped_grads_df = pd.DataFrame(grouped_grads)

        result = closest_city_params(
            uinput_spec_num, uinput_industry, ontology_df, cities_df, grouped_grads_df
        )
        return result.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")