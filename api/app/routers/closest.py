import faulthandler
import geopandas as gpd
import json
import shapely.geometry
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import pandas as pd


from api.app.utils.data_reader import cities
from api.app.methods.methods_get_closest.select_closest_cities import find_n_closest_cities
from api.app.methods.methods_estimate.estimator import do_estimate
from api.app.methods.methods_get_closest.route_api_caller import get_route
from api.app import schemas
from api.app.enums import SpecialtyEnum, IndustryEnum, WorkforceTypeEnum

from api.app.methods.methods_estimate.estimator import do_estimate

faulthandler.enable()

router = APIRouter()

# cities = gpd.read_parquet(
#     "api/app/data/cities.parquet"
# )
# cv = pd.read_parquet('api/app/data/cv.gzip').rename(
#     columns={"hh_name": "specialty"})
# ontology = pd.read_pickle("api/app/data/new_ontology.pkl")

# grouped_grads = pd.read_pickle("api/app/data/grouped_grads.pkl")



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

        """
        Endpoint to retrieve closest cities and their travel routes based on the provided query parameters.
        """
        point_data = query_params.company_location
        # print(point_data)
        point = shapely.geometry.Point(point_data["lon"], point_data["lng"])
        hour_radius = query_params.n_hours

        # Find closest cities
        try:
            closest_cities = find_n_closest_cities(
                point=point, gdf_cities=cities, search_radius_in_h=hour_radius
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Error finding CLOSEST cities: {e}")

        try:
            get_routes = lambda row: get_route(
                start_coords=(point.x, point.y), 
                end_coords=(row.geometry.x, row.geometry.y),  # Accessing geometry using dot notation
                city_name=row.region_city  # Accessing region_city using dot notation
            )

            # Generate the route data, filtering out any None entries
            route_data = list(filter(None, map(get_routes, closest_cities.itertuples(index=False))))
            routes = gpd.GeoDataFrame(route_data, geometry="geometry")
            routes.set_crs(epsg=4326, inplace=True)
            closest_cities.loc[:, "hours"] = routes["duration"].values
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching ROUTES data: {e}")

        try:
            # print(query_params.specialists)
            params, plant_assessment_val = do_estimate(
                uinput_spec_num=query_params.specialists,
                uinput_industry=query_params.industry_name,
                closest_cities=closest_cities)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: ESTIMATOR {e}")

        

        print(plant_assessment_val)

        closest_cities2 = closest_cities.drop(columns=['h3_index']).merge(params, left_on='region_city', right_on='cluster_center', how='left').set_index('region_city')

        # Step 1: Merge the two tables on 'cluster_center' and 'region_city'
        # merged_df = df2.merge(df1, left_on='region_city', right_on='cluster_center', how='left')

        # Step 2: Group by 'region_city' and aggregate specialists and their values into dictionaries
        closest_cities = closest_cities.merge(closest_cities2.groupby('region_city').apply(
            lambda x: {
                row['specialty']: {
                    'prov_graduates': row['prov_graduates'],
                    'prov_specialists': row['prov_specialists'],
                    'total_graduates': row['total_graduates'],
                    'total_specialists': row['total_specialists']
                } for _, row in x.iterrows()
            }
        ).reset_index(name='specialists_data'), on='region_city')

        
        # closest_cities["working_population"] = (
        #     (closest_cities["population"] * WORKING_POPULATION_PERCENT).round(0).fillna(0).astype(int)
        # )

        closest_cities.rename(columns={f'factories_{query_params.industry_name}': 'factories_count', f'graduates_{query_params.industry_name}': 'graduates_count'}, inplace=True)
        closest_cities.drop(columns=['h3_index'], inplace=True)
        # closest_cities['estimate'] = np.mean(closest_cities['specialty']['prov_specialists'], closest_cities['specialty']['prov_graduates'])
        # closest_cities['estimate'] = closest_cities['estimate'].round(3)
        
        
        """Here should be the exact formula of this param calcs"""
        
        

        response = {
            "estimates": json.loads(closest_cities.to_json()),
            "links": json.loads(routes.to_json()),
            "plant": plant_assessment_val
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f":() Analysis failed: {e}")