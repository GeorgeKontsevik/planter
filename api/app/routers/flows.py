from fastapi import APIRouter, status
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
async def calculate_flows(request: FlowRequest1):
    city_name = request.city
    return do_reflow(city_name, {})

@router.post("/custom", status_code=status.HTTP_200_OK)
async def calculate_flows_custom(request: FlowRequest2):
    city_name = request.city
    updated_params = request.updated_params
    
    return do_reflow(city_name, updated_params)