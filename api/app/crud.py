# app/crud.py

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.app import models, schemas
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, shape
import json
from sqlalchemy.orm import joinedload
from sqlalchemy import text
import traceback
from sqlalchemy.dialects.postgresql import insert
from geoalchemy2 import WKTElement

import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

# --- CRUD для Project ---
class ProjectCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_by_id(self, project_id: int):
        stmt = (
            select(models.Project)
            .options(joinedload(models.Project.specialists))  # Eager load specialists
            .filter(models.Project.id == project_id)
        )
        result = await self.db.execute(stmt)
        project = result.unique().scalar_one_or_none()  # Use `.unique()` to handle duplicates
        return project

    async def create_project(self, project_data: dict):
        lng = project_data["company_location"].get("lng")
        lat = project_data["company_location"].get("lat")
        if lng is None or lat is None:
            raise ValueError("Both 'lng' and 'lat' are required in geometry.")

        # Преобразуем координаты в геометрию
        geometry = WKTElement(f"POINT({lng} {lat})", srid=4326)

        # Создаём проект
        new_project = models.Project(
            name=project_data["name"],
            industry_name=project_data.get("industry_name"),
            n_hours=project_data.get("n_hours", 0),
            geometry=geometry
        )
        if "specialists" in project_data:
            new_project.specialists = [
                models.Specialist(specialty=s["specialty"], count=s["count"])
                for s in project_data["specialists"]
            ]
        
        self.db.add(new_project)
        await self.db.commit()
        await self.db.refresh(new_project)
        return {"id":new_project.id, 'name':new_project.name}

    async def update_project_specialists(self, project_id: int, specialists_data: list):
    # Fetch the project
        project = await self.get_project_by_id(project_id)
        if not project:
            return None

        # Update associations
        for s_data in specialists_data:
            # Convert the incoming data to a dictionary if it's not already
            if hasattr(s_data, "dict"):
                s_data = s_data.dict()

            # Find or create the specialist
            result = await self.db.execute(
                select(models.Specialist).filter_by(specialty=s_data["specialty"])
            )
            specialist = result.scalar_one_or_none()

            if not specialist:
                specialist = models.Specialist(specialty=s_data["specialty"])
                self.db.add(specialist)
                await self.db.flush()  # Flush to get the specialist ID



            # Update the association table
            stmt = insert(models.project_specialist_table).values(
                project_id=project.id,
                specialist_id=specialist.id,
                count=s_data["count"]
            ).on_conflict_do_update(
                index_elements=["project_id", "specialist_id"],
                set_={"count": s_data["count"]}
            )

            await self.db.execute(stmt)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def list_projects(self):
        result = await self.db.execute(
            select(models.Project).options(joinedload(models.Project.specialists))
        )
        return result.scalars().all()
# --- CRUD для Layer ---

async def create_layer(db: AsyncSession, layer: schemas.LayerCreate):
    geometry = from_shape(shape(json.loads(layer.geometry)), srid=4326)
    db_layer = models.Layer(
        name=layer.name,
        geometry=geometry,
        properties=layer.properties,
        project_id=layer.project_id
    )
    db.add(db_layer)
    await db.commit()
    await db.refresh(db_layer)
    return db_layer

async def get_layer(db: AsyncSession, layer_id: int):
    result = await db.execute(select(models.Layer).where(models.Layer.id == layer_id))
    return result.scalars().first()

async def update_layer(db: AsyncSession, layer_id: int, layer: schemas.LayerUpdate):
    db_layer = await get_layer(db, layer_id)
    if not db_layer:
        return None
    update_data = layer.dict(exclude_unset=True)
    if 'geometry' in update_data:
        geometry = from_shape(shape(json.loads(update_data['geometry'])), srid=4326)
        update_data['geometry'] = geometry
    for key, value in update_data.items():
        setattr(db_layer, key, value)
    db.add(db_layer)
    await db.commit()
    await db.refresh(db_layer)
    return db_layer

async def delete_layer(db: AsyncSession, layer_id: int):
    db_layer = await get_layer(db, layer_id)
    if not db_layer:
        return None
    await db.delete(db_layer)
    await db.commit()
    return db_layer

async def list_layers(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(models.Layer).offset(skip).limit(limit))
    return result.scalars().all()


# --- CRUD для Data ---
async def create_data(db: AsyncSession, data: schemas.DataCreate):
    db_data = models.Data(**data.dict())
    db.add(db_data)
    await db.commit()
    await db.refresh(db_data)
    return db_data

async def get_data(db: AsyncSession, data_id: int):
    result = await db.execute(
        select(models.Data).where(models.Data.id == data_id)
    )
    return result.scalars().first()

async def update_data(db: AsyncSession, data_id: int, data: schemas.DataUpdate):
    db_data = await get_data(db, data_id)
    if db_data:
        for key, value in data.dict(exclude_unset=True).items():
            setattr(db_data, key, value)
        await db.commit()
        await db.refresh(db_data)
    return db_data

async def delete_data(db: AsyncSession, data_id: int):
    db_data = await get_data(db, data_id)
    if db_data:
        await db.delete(db_data)
        await db.commit()
    return db_data

async def list_data(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(
        select(models.Data).offset(skip).limit(limit)
    )
    return result.scalars().all()
