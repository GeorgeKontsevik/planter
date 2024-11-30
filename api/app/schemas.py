# app/schemas.py

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from .enums import IndustryEnum, SpecialtyEnum
from datetime import datetime




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
    specialty: str  # Corrected from `specialities` to `specialty`
    count: int       # Added `count` to represent the number of specialists

    class Config:
        schema_extra = {
            "example": {
                "specialty": "engineer",
                "count": 5
            }
        }

class ProjectCreate(BaseModel):
    name: str
    industry_name: str
    company_location: Dict[str, float]
    n_hours: int
    specialists: List[SpecialistCreate]

    class Config:
        schema_extra = {
            "example": {
                "name": "Project Alpha",
                "specialists": [
                    {"specialty": "engineer", "count": 5},
                    {"specialty": "manager", "count": 2}
                ],
                "n_hours": 2,
                "industry_name": "aircraft_engineering",
                "company_location": {"lng": 45.128569, "lat": 38.902091}
            }
        }

# Схема для вывода специалистов
class SpecialistOut(BaseModel):
    project: int
    specialty: str
    count: int

# Схема для вывода проекта
class ProjectOut(BaseModel):
    id: int
    name: str
    # specialists: List[SpecialistOut]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Project Alpha",
            }
        }
# Обновление ссылок для Pydantic
Project.update_forward_refs()

# --- Pydantic схемы для Data и Metrics ---


# ------------------------------------------------------

class ClosestCitiesQueryParamsRequest(BaseModel):
    worker_and_count: List
    industry_name: IndustryEnum
    company_location: Dict[str, float]
    n_hours: float

    class Config:
        schema_extra = {
            "example": {
                "industry_name": "aircraft_engineering",
                "company_location": {"lng": 45.128569, "lon": 38.902091},
                "worker_and_count": [
                    {"specialty": "Технолог", "count": 80},
                    {"specialty": "Специалист по сертификации", "count": 50},
                ],
                "n_hours": 1.5,
            }
        }


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


# ------------------------------------------------------
class DataBase(BaseModel):
    key: str
    value: dict  # или Any

class DataCreate(DataBase):
    pass

class DataUpdate(BaseModel):
    key: Optional[str] = None
    value: Optional[dict] = None

class DataRead(DataBase):
    id: int

    class Config:
        orm_mode = True

class MetricsRequest(BaseModel):
    parameter1: float = Field(..., example=10.5)
    parameter2: float = Field(..., example=20.3)


class MetricsResponse(BaseModel):
    metric1: float
    metric2: float

    class Config:
        orm_mode = True


class LayerBase(BaseModel):
    name: str
    geometry: str  # GeoJSON строка
    properties: Optional[dict] = None
    project_id: int  # Связь с Project

class LayerCreate(LayerBase):
    pass

class LayerUpdate(BaseModel):
    name: Optional[str] = None
    geometry: Optional[str] = None
    properties: Optional[dict] = None
    project_id: Optional[int] = None

class Layer(LayerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

