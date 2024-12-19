# app/routers/layers.py

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/layers", tags=["Layers"])

from typing import List, Dict, Union, Any, Optional
from pydantic import BaseModel


@router.post(
    "/",
    # response_model=schemas.LayerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a set of Layers",
    description="Create new layers with geometry and properties."
)
async def create_layer(
    layer_data = Body(...,
                      openapi_examples={
                          "example":{"value":{
            "project_id": 214,
            "name": "Оценка трудовых ресурсов",
            "layers": [
                {
                "name": "Миграционные связи",
                "data": {
                    "type": "FeatureCollection",
                    "features": [
                    {
                        "type": "Feature",
                        "properties": {
                        "distance": 95084.8,
                        "duration": 1.66
                        },
                        "geometry": {
                        "type": "Point",
                        "coordinates": [45.128569, 38.902091]
                        }
                    }
                    ]
                },
                "style": {
                    "fillopacity": 1,
                    "LineWidth": 2,
                    "color": "#35b99"
                }
                },
            ]
            }}}),
    db: AsyncSession = Depends(get_db),
    ):
    """
    Create a new layer for a project.
    """
    layer_crud = crud.LayerCRUD(db)
    new_layer = await layer_crud.create_project_with_layers(layer_data)
    return new_layer

@router.get("/layer/{layer_id}")
async def get_layer(layer_id: int, db: AsyncSession = Depends(get_db)):
    layer_crud = crud.LayerCRUD(db)
    layer = await layer_crud.get_layer_by_id(layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail="Layer not found")
    return layer


@router.get("/listing/{project_id}")
async def get_layers_by_project_id(project_id: int, db: AsyncSession = Depends(get_db)):
    layer_crud = crud.LayerCRUD(db)
    print('\n\n\n\n\n', project_id)
    layers = await layer_crud.get_layers_by_project(project_id)
    if not layers:
        raise HTTPException(status_code=404, detail="No layers found for this project")
    return layers


@router.delete("/layer/{layer_id}", status_code=204)
async def delete_layer(layer_id: int, db: AsyncSession = Depends(get_db)):
    layer_crud = crud.LayerCRUD(db)
    success = await layer_crud.delete_layer(layer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Layer not found")
    return {"detail": "Layer deleted successfully"}


@router.delete("/layer/{project_id}", status_code=204)
async def delete_layers_by_project(project_id: int, db: AsyncSession = Depends(get_db)):
    layer_crud = crud.LayerCRUD(db)
    success = await layer_crud.delete_layers_by_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="No layers found for this project")
    return {"detail": "All layers deleted successfully"}