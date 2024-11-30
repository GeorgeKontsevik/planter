# app/routers/layers.py

from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .. import schemas, crud
from ..database import get_db
from .. import models

from pydantic import BaseModel

router = APIRouter(prefix="/layers", tags=["Layers"])

@router.get("/{layer_id}", response_model=schemas.Layer)
async def get_layer(layer_id: int, db: AsyncSession = Depends(get_db)):
    layer_crud = crud.LayerCRUD(db)
    layer = await layer_crud.get_layer_by_id(layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail="Layer not found")
    return layer


@router.get("/project/{project_id}", response_model=List[schemas.Layer])
async def get_layers_by_project(project_id: int, db: AsyncSession = Depends(get_db)):
    layer_crud = crud.LayerCRUD(db)
    layers = await layer_crud.get_layers_by_project(project_id)
    if not layers:
        raise HTTPException(status_code=404, detail="No layers found for this project")
    return layers



@router.post(
    "/",
    response_model=schemas.LayerResponse,
    status_code=201,
    summary="Create a Layer",
    description="Create a new layer with geometry and properties."
)
async def create_layer(
    layer_data: schemas.LayerCreate = Body(
        ...,
        openapi_examples={
            "default": {
                "summary": "Default example",
                "description": "A default example of a layer with polygon geometry.",
                "value": {
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
                    "project_id": 110
                }
            },
            "minimal": {
                "summary": "Minimal example",
                "description": "A minimal example of a layer with point geometry.",
                "value": {
                    "name": "Simple Layer",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [45.128569, 38.902091]
                    },
                    "project_id": 115
                }
            }
        }
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new layer for a project.
    """
    layer_crud = crud.LayerCRUD(db)
    new_layer = await layer_crud.create_layer(layer_data.dict())
    return new_layer


@router.put("/{layer_id}", response_model=schemas.Layer)
async def update_layer(layer_id: int, layer_data: schemas.LayerUpdate, db: AsyncSession = Depends(get_db)):
    layer_crud = crud.LayerCRUD(db)
    updated_layer = await layer_crud.update_layer(layer_id, layer_data.dict(exclude_unset=True))
    if not updated_layer:
        raise HTTPException(status_code=404, detail="Layer not found")
    return updated_layer


@router.delete("/{layer_id}", status_code=204)
async def delete_layer(layer_id: int, db: AsyncSession = Depends(get_db)):
    layer_crud = crud.LayerCRUD(db)
    success = await layer_crud.delete_layer(layer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Layer not found")
    return {"detail": "Layer deleted successfully"}


@router.delete("/project/{project_id}", status_code=204)
async def delete_layers_by_project(project_id: int, db: AsyncSession = Depends(get_db)):
    layer_crud = crud.LayerCRUD(db)
    success = await layer_crud.delete_layers_by_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="No layers found for this project")
    return {"detail": "All layers deleted successfully"}