from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from pydantic import BaseModel
from typing import Dict, Optional
import os
import pickle
import geopandas as gpd
from api.app.methods.workflows import WorkForceFlows  # Replace with the correct module name

import __main__
__main__.WorkForceFlows = WorkForceFlows

DEGREE_CRS = 4326
METRIC_CRS = 3857

router = APIRouter(
    prefix="/flows",
    tags=["City"],
)

# Load or initialize WorkForceFlows
filename = "wff_model_1711.pkl"
directory = "api/app/data"


# Check if the file exists in the specified directory

if filename in os.listdir(directory):
    
    filepath = os.path.join(directory, 'scaler_wff.pkl')
    with open(filepath, "rb") as f:
        scaler_x = pickle.load(f)

    filepath = os.path.join(directory, 'gravity_wff.pkl')
    with open(filepath, "rb") as f:
        model_gravity = pickle.load(f)

    filepath = os.path.join(directory, 'cities.parquet')
    cities = gpd.read_parquet(filepath)

    
    filepath = os.path.join(directory, filename)
    wff = WorkForceFlows.from_pickle(filepath)
    wff['cities'] = cities
    wff['scaler'] = scaler_x
    wff['model'] = model_gravity
    
    
else:
    raise FileNotFoundError(f"The file {filename} was not found in the directory {directory}.")

# Input model
class FlowRequest(BaseModel):
    city: str  # City name
    updated_params: Optional[Dict[str, float]] = None  # Example: {"median_salary": 40000}

@router.post("/", status_code=status.HTTP_200_OK)
async def calculate_flows(request: FlowRequest):
    city_name = request.city
    updated_params = request.updated_params
    area = wff.initial_cities_state.loc[wff.initial_cities_state['region_city']==city_name, 'geometry'].to_frame().to_crs(METRIC_CRS).buffer(200*1e3).to_crs(DEGREE_CRS).to_frame()

    try:
        # Update parameters and recalculate if needed
        if updated_params:
            wff.update_city_params(city_name, updated_params)
            wff.recalculate_after_update()

            # Generate differences
            diff = wff.compare_city_states()
            diff_links = wff.compare_link_states()

            # Apply masks and save GeoJSONs
            mask = diff["in_out_diff"] != -10
            cities_diff = diff[mask].dropna().clip(area)

            mask_links = diff_links["big_flows"] > 0
            links_diff = wff.gdf_links[wff.gdf_links["destination"].isin(diff_links[mask_links]["destination"])]

            return {
                "cities_diff": cities_diff.to_json(),
                "links_diff": links_diff.to_json(),
            }

        # Return original flows without updates
        else:
            # print(area)
            original_cities = wff.cities.to_crs(DEGREE_CRS).overlay(area)

            original_flows_mask = wff.gdf_links['destination'].isin(original_cities['region_city'])

            original_flows = wff.gdf_links[original_flows_mask]

            # print(original_cities)
            return {"original_cities": original_cities.to_json(),
                    'original_flows': original_flows.to_json()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))