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

@router.get("/", summary="Get indo about specilists' educational groups", status_code=status.HTTP_200_OK)
async def get_edu_groups():
    # mask = (ontology['speciality'].isin(specialities_list))
    res = ontology.loc[:, ['speciality', 'edu_group_code', 'edu_group', 'prof_domain']]

    grouped_extended_df = res.groupby(['speciality', 'edu_group_code']).agg({
        'edu_group': lambda x: list(x.dropna().unique()),
        'prof_domain': lambda x: list(x.dropna().unique())
    }).reset_index()

    # Convert to JSON
    final_extended_data = grouped_extended_df.to_dict(orient='records')
    json_extended_output = json.loads(json.dumps(final_extended_data, ensure_ascii=False, indent=2))

    return json_extended_output
