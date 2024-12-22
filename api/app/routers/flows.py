from fastapi import APIRouter, status,Body
from pydantic import BaseModel
from typing import Dict, Optional
from api.app.methods.workflows import do_reflow  # Replace with the correct module name

router = APIRouter(
    prefix="/flows",
    tags=["City"],
)

# Input model
class FlowRequest1(BaseModel):
    city: str  # City name

# Input model
class FlowRequest2(BaseModel):
    city: str  # City name
    updated_params: Optional[Dict[str, float]] = None  # Example: {"median_salary": 40000}

@router.post("/", status_code=status.HTTP_200_OK)
async def calculate_flows(request=Body(...)):
    city_name = request["city"]
    # industry = request["industry_name"]
    # specs = request["specialists"]
    return do_reflow(city_name, {})

@router.post("/custom", status_code=status.HTTP_200_OK)
async def calculate_flows_custom(request=Body(...)):
    city_name = request["city"]
    updated_params = request["updated_params"]
    industry = request["industry_name"]
    if industry=='wood_processing':
        industry='chemicals'
    specs = request["specialists"]


    workforce_type = request.get('workforce_type', None)
    list_cities_names = []
    print('\n\n\n\n\n\n\n\n\n',request.get('cities_with_params'))
    for i in request['cities_with_params']:
        list_cities_names.append(list(i.keys())[0])
    
    return do_reflow(city_name, updated_params, industry, specs, workforce_type, list_cities_names=list_cities_names)