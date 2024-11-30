# app/routers/layers.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .. import schemas, crud
from ..database import get_db

router = APIRouter(
    prefix="/layers",
    tags=["Layers"],
)

@router.post("/", response_model=schemas.Layer, status_code=status.HTTP_201_CREATED)
async def create_layer(layer: schemas.LayerCreate, db: AsyncSession = Depends(get_db)):
    db_layer = await crud.create_layer(db, layer)
    return db_layer

@router.get("/{layer_id}", response_model=schemas.Layer, tags=["Layers"])
async def read_layer(layer_id: int, db: AsyncSession = Depends(get_db)):
    db_layer = await crud.get_layer(db, layer_id)
    if db_layer is None:
        raise HTTPException(status_code=404, detail="Layer not found")
    return db_layer

@router.put("/{layer_id}", response_model=schemas.Layer, tags=["Layers"])
async def update_layer(layer_id: int, layer: schemas.LayerUpdate, db: AsyncSession = Depends(get_db)):
    db_layer = await crud.update_layer(db, layer_id, layer)
    if db_layer is None:
        raise HTTPException(status_code=404, detail="Layer not found")
    return db_layer

@router.delete("/{layer_id}", response_model=schemas.Layer, tags=["Layers"])
async def delete_layer(layer_id: int, db: AsyncSession = Depends(get_db)):
    db_layer = await crud.delete_layer(db, layer_id)
    if db_layer is None:
        raise HTTPException(status_code=404, detail="Layer not found")
    return db_layer

@router.get("/", response_model=List[schemas.Layer], tags=["Layers"])
async def list_layers(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    layers = await crud.list_layers(db, skip=skip, limit=limit)
    return layers