# app/routers/projects.py

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, delete
from api.app.models import Specialist
from typing import List, Union, Dict, Optional, Any
from enum import Enum

from pydantic import BaseModel

from .. import schemas, crud
from ..database import get_db
from .. import models

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)
# Стили
class CSSProperties(BaseModel):
    color: str
    radius: float
    width: float
    fillColor: str
    strokeColor: str
    # Add other styles as needed

# Геометрия
class FeatureGeometry(BaseModel):
    type: str  # 'Point', 'LineString', 'Polygon'
    coordinates: Any  # Coordinate array depending on the geometry type

# Свойства геометрии
class FeatureProperties(BaseModel):
    pass  # Can contain any keys and values

# Особенности
class Feature(BaseModel):
    id: str
    type: str  # 'Feature'
    geometry: FeatureGeometry
    properties: FeatureProperties

# Коллекция особенностей
class FeatureCollection(BaseModel):
    type: str  # 'FeatureCollection'
    features: List[Feature]

# Слой
class Layer(BaseModel):
    name: str
    style: Optional[CSSProperties] = None  # Optional
    data: FeatureCollection

# Группа слоев
class GroupLayer(BaseModel):
    name: str
    project_id: int
    layers: List[Layer]

# Ответ с группами слоев
GroupLayersResponse = List[GroupLayer]

# # Специалист
# class SpecialistP(BaseModel):
#     id: int
#     name: str
#     role: str
#     experience_years: float

# # Ответ от сервера /everything
# class Response(BaseModel):
#     geometry: Dict[str, Union[str, List[float]]]
#     id: int
#     industry_name: str
#     layers: GroupLayersResponse
#     n_hours: float
#     name: str
#     specialists: List[SpecialistP]
#     workforce_type: str



@router.post("/", summary="Create new project", response_model=schemas.ProjectInOut, status_code=status.HTTP_201_CREATED)
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
                        "company_location": {"lng": 45.128569, 
                                             "lat": 38.902091},
                        "workforce_type": "graduates",
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

    return db_project


@router.get("/list",
    # response_model=schemas.ProjectSummary,
    summary="List projects",
    response_model=List[schemas.ProjectSummary],
    description="Retrieve basic project details such as id, name and industry",)
async def list_projects(db: AsyncSession = Depends(get_db)):
    """
    Endpoint to list all projects with their ID, name, and industry.
    """
    stmt = select(models.Project.id, models.Project.name, models.Project.industry_name)
    result = await db.execute(stmt)
    projects = result.fetchall()
    return [{"id": p.id, "name": p.name, "industry_name": p.industry_name} for p in projects]


# Получение проекта по ID
@router.get(
    "/{project_id}",
    # response_model=schemas.ProjectOut,
    summary="Get project by ID",
    description="Retrieve project details along with associated specialists",
    )
async def get_project(project_id: int,
                    db: AsyncSession = Depends(get_db)):

    specialist_crud_instance = crud.SpecialistCRUD(db)
    # Fetch related entities
    specialists = await specialist_crud_instance.get_specialists_by_project_id(project_id)

    # Fetch project
    proj_crud_instance = crud.ProjectCRUD(db)
    project = await proj_crud_instance.get_project_by_id(project_id)
    project.geometry = crud.serialize_geometry(project.geometry)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Assemble the response
    return {
        "id": project.id,
        "name": project.name,
        "industry_name": project.industry_name,
        "n_hours": project.n_hours,
        "workforce_type": project.workforce_type,
        "geometry": project.geometry,
        "specialists": specialists,
    }


    # proj_crud_instance = crud.ProjectCRUD(db)
    # project = await proj_crud_instance.get_project_by_id(project_id)
    # if not project:
    #     raise HTTPException(status_code=404, detail="Project not found")
    # project.geometry = crud.serialize_geometry(project.geometry)
    # return project




@router.put("/projects/specialists/{project_id}")
async def modify_specialists(
    project_id: int,
    payload: schemas.ModifySpecialistsRequest = Body(..., openapi_examples={
                "example1": {
                    "summary": "A typical example",
                    "description": "An example of a project creation request.",
                    "value": {
                            "add": [
                                {"specialty": "Оператор, аппаратчик", "count": 3},
                                {"specialty": "Сварщик", "count": 2}
                            ],
                            "update": [
                                {"id": 333, "count": 5}
                            ],
                            "delete": [335]
                            }
                            }
                            }
                            ),
    db: AsyncSession = Depends(get_db)
    ):
    """
    Modify specialists for a project:
    - Add new specialists or update on conflict
    - Update existing specialists
    - Delete specialists by ID
    """
    # try:
    # Process additions with upsert (insert or update on conflict)
    if payload.add:
        for specialist in payload.add:
            stmt_add = insert(Specialist).values(
                project_id=project_id,
                specialty=specialist.specialty.value,  # Convert Enum to string
                count=specialist.count,
            ).on_conflict_do_update(
                index_elements=["project_id", "specialty"],  # Conflict on project_id + specialty
                set_={"count": specialist.count}  # Update the `count` field on conflict
            )
            await db.execute(stmt_add)

    # Process updates
    if payload.update:
        for specialist in payload.update:
            update_data = {
                k: (v.value if isinstance(v, Enum) else v)  # Convert Enum to string if present
                for k, v in specialist.dict().items()
                if k != "id" and v is not None  # Exclude None and id
            }
            stmt_update = (
                update(Specialist)
                .where(Specialist.id == specialist.id)
                .values(**update_data)
            )
            result = await db.execute(stmt_update)
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Specialist with ID {specialist.id} not found."
                )

    # Process deletions
    if payload.delete:
        stmt_delete = delete(Specialist).where(Specialist.id.in_(payload.delete))
        await db.execute(stmt_delete)

    # Commit changes
    await db.commit()

    return {"message": "Specialists modified successfully"}

    # except Exception as e:
    #     await db.rollback()
    #     raise HTTPException(status_code=500, detail=f"Error modifying specialists: {str(e)}")

@router.put("/{project_id}", summary="Update project parameters", response_model=schemas.ProjectInOut)
async def update_project(
    project_id: int,
    project: schemas.ProjectCreate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a project's parameters by ID and manage its related specialists.
    """
    # try:
    # Initialize warnings for specialist updates and deletions
    warnings = {"specialists_update": [], "specialists_delete": []}

    # Initialize CRUD instances
    project_crud = crud.ProjectCRUD(db)
    specialist_crud = crud.SpecialistCRUD(db)

    # Check if the project exists
    existing_project = await project_crud.get_project_by_id(project_id)
    if not existing_project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Update project fields
    project_data = project.dict()
    

    # Process specialists (handle add, update, and delete)
    if "specialists" in project_data:
        specialists_payload = project_data["specialists"]

        # Fetch existing specialists for this project
        existing_specialists = await specialist_crud.get_specialists_by_project_id(project_id)
        existing_specialties = {spec.specialty: spec for spec in existing_specialists}

        # Add or update specialists
        new_specialties = {spec["specialty"]: spec for spec in specialists_payload}
        for specialty, spec_data in new_specialties.items():
            if specialty in existing_specialties:
                # Update existing specialist
                stmt_update = (
                    update(models.Specialist)
                    .where(
                        models.Specialist.project_id == project_id,
                        models.Specialist.specialty == specialty,
                    )
                    .values(count=spec_data["count"])
                )
                result = await db.execute(stmt_update)
                if result.rowcount == 0:
                    warnings["specialists_update"].append(specialty)
            else:
                # Add new specialist
                stmt_add = insert(models.Specialist).values(
                    project_id=project_id,
                    specialty=specialty,
                    count=spec_data["count"],
                )
                await db.execute(stmt_add)

        # Delete specialists not in the new list
        specialties_to_delete = set(existing_specialties.keys()) - set(new_specialties.keys())
        for specialty in specialties_to_delete:
            stmt_delete = (
                delete(models.Specialist)
                .where(
                    models.Specialist.project_id == project_id,
                    models.Specialist.specialty == specialty,
                )
            )
            result = await db.execute(stmt_delete)
            if result.rowcount == 0:
                warnings["specialists_delete"].append(specialty)

    project_fields = {k: v for k, v in project_data.items() if k != "specialists"}
    await project_crud.update_project(project_id, project_fields)

    # Commit all changes
    await db.commit()

    # Fetch updated project
    updated_project = await project_crud.get_project_by_id(project_id)
    print(warnings)

    # Return updated project with warnings
    return {"id": updated_project.id, "name": updated_project.name}

@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    proj_crud_instance = crud.ProjectCRUD(db)
    success = await proj_crud_instance.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"detail": "Project deleted successfully"}

@router.get(
    "/{project_id}/everything",
    # response_model=schemas.ProjectEverything,
    summary="Get everything for a project",
    description="Retrieve project details including specialists, layers, and other related entities",
)
async def get_project_everything(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    
    
    specialist_crud_instance = crud.SpecialistCRUD(db)
    # Fetch related entities
    specialists = await specialist_crud_instance.get_specialists_by_project_id(project_id)

    layer_crud_instance = crud.LayerCRUD(db)
    layers = await layer_crud_instance.get_layers_by_project(project_id)

    # try:
    #     # Validate the layers data
    #     [GroupLayer(**group) for group in layers]
    #     # return validated_layers
    # except Exception as e:
    #     # Handle validation errors
    #     raise HTTPException(status_code=400, detail=f"Invalid layer data: {str(e)}")

    # Fetch project
    proj_crud_instance = crud.ProjectCRUD(db)
    project = await proj_crud_instance.get_project_by_id(project_id)
    project.geometry = crud.serialize_geometry(project.geometry)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # print(layers)
    # print(list(layers.values())[0])

    # Assemble the response
    return {
        "id": project.id,
        "name": project.name,
        "industry_name": project.industry_name,
        "n_hours": project.n_hours,
        "workforce_type": project.workforce_type,
        "geometry": project.geometry,
        "layer_groups": list(layers.values())[0],
        "specialists": specialists,
    }
