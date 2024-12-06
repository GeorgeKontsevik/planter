# app/routers/projects.py

from fastapi import APIRouter, status
from typing import List
from api.app.enums import SpecialtyEnum, IndustryEnum
import pandas as pd
import json

router = APIRouter(
    prefix="/tools",
    tags=["Tooltip"],
)

ontology = pd.read_pickle('api/app/data/new_ontology.pkl')

@router.post("/", summary="Get indo about specilists' educational groups", status_code=status.HTTP_200_OK)
async def get_edu_groups(industry: IndustryEnum, specialities_list: List[SpecialtyEnum]):
    mask = (ontology['industry_code'] == industry) & (ontology['speciality'].isin(specialities_list))
    res = ontology.loc[mask, ['speciality', 'edu_group_code', 'edu_group', 'prof_domain']]
    return json.loads(res.to_json())