# app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from .enums import IndustryEnum, SpecialtyEnum, WorkforceTypeEnum
from datetime import datetime



class LayerBase(BaseModel):
    name: str
    geometry: Dict  # GeoJSON-like structure
    properties: Optional[Dict] = None


class LayerCreate(LayerBase):
    project_id: int

    class Config:
        schema_extra = {
            "example": {
                "name": "Building Footprint",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [45.128569, 38.902091],
                            [45.129569, 38.903091],
                            [45.130569, 38.901091],
                            [45.128569, 38.902091]
                        ]
                    ]
                },
                "properties": {
                    "color": "blue",
                    "material": "concrete"
                },
                "project_id": 1
            }
        }


class LayerUpdate(BaseModel):
    name: Optional[str]
    geometry: Optional[Dict]
    properties: Optional[Dict]

    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Layer Name",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [45.128569, 38.902091],
                            [45.129569, 38.903091],
                            [45.130569, 38.901091],
                            [45.128569, 38.902091]
                        ]
                    ]
                },
                "properties": {
                    "color": "red",
                    "material": "steel"
                }
            }
        }


class Layer(LayerBase):
    id: int
    project_id: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 10,
                "name": "Layer Example",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [45.128569, 38.902091],
                            [45.129569, 38.903091],
                            [45.130569, 38.901091],
                            [45.128569, 38.902091]
                        ]
                    ]
                },
                "properties": {
                    "key": "value"
                },
                "project_id": 1
            }
        }


class LayerResponse(BaseModel):
    id: int
    name: str
    project_id: int

    class Config:
        orm_mode = True

class LayerOut(BaseModel):
    id: int
    name: str
    geometry: Dict[str, Any]  # GeoJSON format
    properties: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True
# -------------

class ProjectBase(BaseModel):
    name: Optional[str] = Field(default="Default Project Name")
    industry_name: IndustryEnum


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    industry_name: Optional[str] = None
    company_location: Optional[Dict[str, float]] = None
    n_hours: Optional[int] = None


class Project(ProjectBase):
    id: int
    updated_at: datetime

    class Config:
        orm_mode = True

class SpecialistCreate(BaseModel):
    specialty: SpecialtyEnum  # Corrected from `specialities` to `specialty`
    count: int       # Added `count` to represent the number of specialists

    class Config:
        schema_extra = {
            "example": {
                "specialty": "Оператор, аппаратчик",
                "count": 5
            }
        }

class ProjectCreate(BaseModel):
    name: str
    industry_name: str
    company_location: Dict[str, float]
    n_hours: float = Field(..., lt=3)
    specialists: List[SpecialistCreate]
    workforce_type: WorkforceTypeEnum

    class Config:
        schema_extra = {
            "example": {
                "name": "Project Alpha",
                "specialists": [
                    {"specialty": "engineer", "count": 5},
                    {"specialty": "manager", "count": 2}
                ],
                "workforce_type":"all",
                "n_hours": 2,
                "industry_name": "aircraft_engineering",
                "company_location": {"lng": 45.128569, "lat": 38.902091}
            }
        }

class SpecialistOut(BaseModel):
    id: int
    specialty: str
    count: int
    project_id: int  # Explicitly add project_id instead of the full Project object

    class Config:
        orm_mode = True

# Схема для вывода проекта
class ProjectOut(BaseModel):
    id: int
    name: str
    industry_name: str
    n_hours:float
    geometry: Any  # GeoJSON format
    # specialists: List[SpecialistOut]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Project Alpha",
                "industry_name": "Very High Tech Industry",
                "n_hours":1
            }
        }
# Обновление ссылок для Pydantic

class ProjectEverything(BaseModel):
    id: int
    name: str
    industry_name: Optional[str]
    n_hours: int
    specialists: List[SpecialistOut]
    layers: List[LayerOut]

    class Config:
        orm_mode = True

class ProjectInOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class ProjectSummary(BaseModel):
    id: int
    name: str
    industry_name: str

    class Config:
        orm_mode = True

Project.update_forward_refs()

# --- Pydantic схемы для LAYERS --



# ------------------------------------------------------

class ClosestCitiesQueryParamsRequest(BaseModel):
    specialists: List[Dict[str, Union[SpecialtyEnum, int]]] = Field(
        ...,
        example=[
            {"specialty": "technologist", "count": 80},
            {"specialty": "certification_specialist", "count": 50},
        ],
    )
    industry_name: IndustryEnum = Field(..., example="shipbuilding")
    company_location: Dict[str, float] = Field(
        ...,
        example={"lng": 45.128569, "lon": 38.902091},
    )
    n_hours: float = Field(..., example=1.5, lt=3)


class UpdateParams(BaseModel):
    median_salary: Optional[float] = None
    ueqi_residential: Optional[float] = None
    ueqi_street_networks: Optional[float] = None
    ueqi_green_spaces: Optional[float] = None
    ueqi_public_and_business_infrastructure: Optional[float] = None
    ueqi_social_and_leisure_infrastructure: Optional[float] = None
    ueqi_citywide_space: Optional[float] = None


class OptimizeRequest(BaseModel):
    name: str
    new_params: UpdateParams


class OptimizeResponse(BaseModel):
    initial_migration: float
    optimized_migration: float
    optimal_parameters: Dict[str, float]

class SpecialistAdd(BaseModel):
    specialty: SpecialtyEnum
    count: int

class SpecialistUpdate(BaseModel):
    id: int
    specialty: Optional[SpecialtyEnum] = None
    count: Optional[int] = None

class ModifySpecialistsRequest(BaseModel):
    add: List[SpecialistAdd] = []
    update: List[SpecialistUpdate] = []
    delete: List[int] = []