# app/routers/projects.py

from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .. import schemas, crud
from ..database import get_db
from .. import models

from pydantic import BaseModel

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post("/", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: schemas.ProjectCreate = Body(
            ...,
            openapi_examples={
                "example1": {
                    "summary": "A typical example",
                    "description": "An example of a project creation request.",
                    "value": {
                        'name': 'gigafactory',
                        "industry_name": "aircraft_engineering",
                        "company_location": {"lng": 45.128569, "lat": 38.902091},
                        "n_hours": 2,
                        "specialists": [
                            {"specialty": "engineer", "count": 5},
                            {"specialty": "manager", "count": 2}
                        ],
                    },
                },
            },
        ),
        db: AsyncSession = Depends(get_db),
    ):

    project = project.dict()

    proj_crud_instance = crud.ProjectCRUD(db)
    db_project = await proj_crud_instance.create_project(project)
    print(db_project)
    return db_project

# Получение проекта по ID
@router.get(
    "/projects/{project_id}",
    response_model=schemas.ProjectOut,
    summary="Get project by ID",
    description="Retrieve project details along with associated specialists",
    )
async def get_project(project_id: int,
                    db: AsyncSession = Depends(get_db)):
    proj_crud_instance = crud.ProjectCRUD(db)
    project = await proj_crud_instance.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project



@router.put(
    "/projects/{project_id}/specialists",
    # response_model=schemas.ProjectOut,
    summary="Update project specialists",
    description="Assign specialists to a project and update their counts."
)
async def update_project_specialists(
    project_id: int,
    specialists_data: List[schemas.SpecialistCreate],
    db: AsyncSession = Depends(get_db),
):
    proj_crud_instance = crud.ProjectCRUD(db)
    await proj_crud_instance.update_project_specialists(project_id, specialists_data)
    return None


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    proj_crud_instance = crud.ProjectCRUD(db)
    success = await proj_crud_instance.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"detail": "Project deleted successfully"}

@router.get(
    "/projects/{project_id}/everything",
    response_model=schemas.ProjectEverything,
    summary="Get everything for a project",
    description="Retrieve project details including specialists, layers, and other related entities",
)
async def get_project_everything(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    proj_crud_instance = crud.ProjectCRUD(db)
    layer_crud_instance = crud.LayerCRUD(db)
    specialist_crud_instance = crud.SpecialistCRUD(db)

    # Fetch project
    project = await proj_crud_instance.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch related entities
    specialists = await specialist_crud_instance.get_specialists_by_project_id(project_id)
    layers = await layer_crud_instance.get_layers_by_project(project_id)

    # Assemble the response
    return {
        "id": project.id,
        "name": project.name,
        "industry_name": project.industry_name,
        "n_hours": project.n_hours,
        "specialists": specialists,
        "layers": layers,
    }

# Список всех проектов
# @router.get(
#     "/projects/",
#     response_model=list[schemas.ProjectOut],
#     summary="Get all projects",
#     description="Retrieve a list of all projects with their specialists",
# )
# async def list_projects(db: AsyncSession = Depends(get_db)):
#     """
#     Получает список всех проектов и их специалистов.
#     """
#     proj_crud_instance = crud.ProjectCRUD(db)
#     projects = await proj_crud_instance.list_projects()
#     return projects