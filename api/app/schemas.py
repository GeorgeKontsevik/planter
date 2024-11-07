from api.app.enums import IndustryEnums
import json

from pydantic import BaseModel, root_validator, conint
from geojson_pydantic import FeatureCollection

from typing import Optional, List, Dict


class ClosestCitiesQueryParams(BaseModel):
    worker_and_count: List
    industry_name: IndustryEnums
    company_location: Dict[str, float]
    n_hours: float

    class Config:
        schema_extra = {
            "example": {
                "industry_name": "Авиастроение и космическая отрасль",
                "company_location": {"lon": 45.128569, "lat": 38.902091},
                "worker_and_count": [
                    {"speciality": "Технолог", "count": 80},
                    {"speciality": "Специалист по сертификации", "count": 50},
                ],
                "n_hours": 1.5,
            }
        }
