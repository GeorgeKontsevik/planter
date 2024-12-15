import faulthandler
import geopandas as gpd
import json
import shapely.geometry

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Dict
import pandas as pd


from api.app.utils.data_reader import cities
from api.app.methods.methods_get_closest.select_closest_cities import find_n_closest_cities
from api.app.methods.methods_estimate.estimator import closest_city_params
from api.app.methods.methods_get_closest.route_api_caller import get_route
from api.app import schemas
from api.app.enums import SpecialtyEnum, IndustryEnum, WorkforceTypeEnum

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
def get_closest_cities(query_params: schemas.ClosestCitiesQueryParamsRequest,
    workforce_type: WorkforceTypeEnum = 'graduates'):
    try:
        # ontology: dict,  # Convert this to a DataFrame before passing to the function
        # cities: dict,  # Convert this to a DataFrame before passing to the function
        # grouped_grads: dict,  # Convert this to a DataFrame before passing to the function):
        """
        Endpoint to retrieve closest cities and their travel routes based on the provided query parameters.
        """
        point_data = query_params.company_location
        print(point_data)
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

        try:
            ontology_df = pd.DataFrame(ontology)
            cities_df = pd.DataFrame(cities)
            grouped_grads_df = pd.DataFrame(grouped_grads)

            params = closest_city_params(
                query_params.specialists, query_params.industry_name, grouped_grads_df, ontology_df, cities_df
            ).reset_index(drop=False).drop(columns=['factories_total', 'population'])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
        # print(params)

        map_workforce = {
            'specialists': ['CV'],
            'graduates': ['ВПО'],
            'all': ['CV', 'ВПО']
        }
        mask_type_workforce = params['type'].isin(map_workforce[workforce_type])
        mask_cities = params['cluster_center'].isin(closest_cities['region_city'])
        params = params[mask_type_workforce & mask_cities]

            # Prepare the response
        WORKING_POPULATION_PERCENT = .65
        closest_cities = closest_cities.drop(columns=['h3_index']).merge(params, left_on='region_city', right_on='cluster_center', how='left')
        closest_cities["working_population"] = (
            (closest_cities["population"] * WORKING_POPULATION_PERCENT).round(0).fillna(0).astype(int)
        )

        closest_cities.rename(columns={f'factories_{query_params.industry_name}': 'factories_count', f'graduates_{query_params.industry_name}': 'graduates_count'}, inplace=True)
        
        """Here should be the exact formula of this param calcs"""
        plant_assessment_val = 1

        print(closest_cities.columns)

        response = {
            "estimates": json.loads(closest_cities.to_json()),
            "links": json.loads(routes.to_json()),
            "metric_float": plant_assessment_val
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"\n\n\n\n\n\n\n\nAnalysis failed: {e}")