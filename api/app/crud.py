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

        # Convert coordinates to geometry
        geometry = WKTElement(f"POINT({lng} {lat})", srid=4326)

        # Create the project
        new_project = models.Project(
            name=project_data["name"],
            industry_name=project_data.get("industry_name"),
            n_hours=project_data.get("n_hours", 0),
            geometry=geometry,
        )

        self.db.add(new_project)
        await self.db.commit()

        # Add specialists with counts to the project_specialist table
        if "specialists" in project_data:
            for s in project_data["specialists"]:
                # Insert or retrieve the specialist
                stmt_specialist = insert(models.Specialist).values(
                    specialty=s["specialty"], count=s["count"], project_id = new_project.id
                ).on_conflict_do_nothing()  # Ignore if the specialty already exists
                await self.db.execute(stmt_specialist)

        await self.db.commit()
        await self.db.refresh(new_project)
        return {"id": new_project.id, "name": new_project.name}

    async def update_project_specialists(self, project_id: int, specialists_data: list):
    # Fetch the project
        project = await self.get_project_by_id(project_id)
        if not project:
            return None

        for s_data in specialists_data:
            # Ensure uniqueness in the specialists table
            stmt_specialist = insert(models.Specialist).values(
                specialty=s_data["specialty"]
            ).on_conflict_do_nothing()  # Ignore if the specialty already exists
            await self.db.execute(stmt_specialist)

            # Retrieve the specialist ID (after insert or from existing entry)
            await self.db.execute(
                select(models.Specialist).where(models.Specialist.specialty == s_data["specialty"])
            ).on_conflict_do_update(
                index_elements=["project_id", "id"],  # Composite unique key
                set_={"count": s_data["count"]}
            )

        await self.db.commit()
        await self.db.refresh(project)
        return project
    
    async def delete_project(self, project_id: int):
        # Fetch the project
        project = await self.get_project_by_id(project_id)
        if not project:
            return None  # Project doesn't exist

        # Delete the project
        await self.db.delete(project)
        await self.db.commit()
        return True
    
    async def get_project_with_everything(self, project_id: int):
        stmt = (
            select(models.Project)
            .options(
                joinedload(models.Project.specialists),  # Load specialists
                joinedload(models.Project.layers),       # Load layers
                # Add any additional relationships here if needed
            )
            .filter(models.Project.id == project_id)
        )
        result = await self.db.execute(stmt)
        project = result.unique().scalar_one_or_none()  # Use `.unique()` to avoid duplicates
        return project

    # async def list_projects(self):
    #     result = await self.db.execute(
    #         select(models.Project).options(joinedload(models.Project.specialists))
    #     )
    #     return result.scalars().all()
# --- CRUD для Layer ---

class LayerCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_layer_by_id(self, layer_id: int):
        # Fetch a single layer by ID
        result = await self.db.execute(
            select(models.Layer).filter(models.Layer.id == layer_id)
        )
        return result.scalar_one_or_none()

    async def get_layers_by_project(self, project_id: int):
        # Fetch all layers associated with a specific project
        result = await self.db.execute(
            select(models.Layer).filter(models.Layer.project_id == project_id)
        )
        return result.scalars().all()

    async def create_layer(self, layer_data: dict):
        
        # Convert GeoJSON geometry to WKT
        geojson_geometry = layer_data["geometry"]
        shapely_geometry = shape(geojson_geometry)
        wkt_geometry = WKTElement(shapely_geometry.wkt, srid=4326)

        # Replace the GeoJSON geometry with WKT
        layer_data["geometry"] = wkt_geometry

        # Create a new layer
        new_layer = models.Layer(**layer_data)
        
        self.db.add(new_layer)
        await self.db.commit()
        await self.db.refresh(new_layer)

        return {
            "id": new_layer.id,
            "name": new_layer.name,
            "project_id": new_layer.project_id
            }

    # async def update_layer(self, layer_id: int, updated_data: dict):
    #     # Update a specific layer
    #     layer = await self.get_layer_by_id(layer_id)
    #     if not layer:
    #         return None

    #     for key, value in updated_data.items():
    #         setattr(layer, key, value)

    #     await self.db.commit()
    #     await self.db.refresh(layer)
    #     return layer

    async def delete_layer(self, layer_id: int):
        # Delete a single layer
        layer = await self.get_layer_by_id(layer_id)
        if not layer:
            return None

        await self.db.delete(layer)
        await self.db.commit()
        return True

    async def delete_layers_by_project(self, project_id: int):
        # Delete all layers associated with a project
        layers = await self.get_layers_by_project(project_id)
        if not layers:
            return None

        for layer in layers:
            await self.db.delete(layer)
        await self.db.commit()
        return True
