# app/crud.py

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.app import models, schemas
from geoalchemy2.shape import to_shape
from shapely.geometry import shape 
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.postgresql import insert
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import mapping
from sqlalchemy import update
from fastapi import HTTPException
import uuid

import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

def serialize_geometry(geometry):
    if geometry:
        return mapping(to_shape(geometry))  # Convert to GeoJSON-like dictionary
    return None

# --- CRUD для Project ---
class ProjectCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_by_id(self, project_id: int):
        stmt = (
            select(models.Project)
            .options(joinedload(models.Project.specialists))  # Eager load specialists
            .filter(models.Project.id == project_id)
        ).execution_options(autocommit=True)

        result = await self.db.execute(stmt)
        project = result.unique().scalar_one_or_none()  # Use `.unique()` to handle duplicates
        # if project:
        #     project.geometry = serialize_geometry(project.geometry)
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
            workforce_type=project_data.get('workforce_type')
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

    async def update_project_specialists(self, project_id: dict, specialists_data: list):
        # Fetch the project

        for s_data in specialists_data:
            s_data = s_data.dict()
            # Ensure uniqueness in the specialists table
            stmt_specialist = insert(models.Specialist).values(
                specialty=s_data["specialty"], project_id=project_id,
                count = s_data['count']
            ).on_conflict_do_update(
            index_elements=["specialty", "project_id"],  # Ensure uniqueness
            set_={
                "count": s_data['count']
            })  # Ignore if the specialty already exists
            await self.db.execute(stmt_specialist)

            await self.db.commit()
        # await self.db.refresh(project)

        return 1
    
    async def delete_project(self, project_id: int):
        # Fetch the project
        project = await self.get_project_by_id(project_id)
        if not project:
            return None  # Project doesn't exist

        # Delete the project
        await self.db.delete(project)
        await self.db.commit()
        return True
    
    async def update_project(self, project_id: int, fields: dict):
        """
        Update a project's fields by ID.
        """
        lng = fields["company_location"].get("lng")
        lat = fields["company_location"].get("lat")
        if lng is None or lat is None:
            raise ValueError("Both 'lng' and 'lat' are required in geometry.")

        # Convert coordinates to geometry
        fields['geometry'] = WKTElement(f"POINT({lng} {lat})", srid=4326)
        del fields["company_location"]

        stmt = (
            update(models.Project)
            .where(models.Project.id == project_id)
            .values(**fields)
        )
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found.")
        return result.rowcount

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
        layer = result.scalar_one_or_none()
        if layer:
            # Serialize geometry to GeoJSON
            layer.geometry = to_shape(layer.geometry).__geo_interface__
        return layer

    async def generate_unique_group_id(self, project_id: int):
        # Fetch all layers associated with the project
        result = await self.db.execute(
            select(models.Layer.group_id).filter(models.Layer.project_id == project_id)
        )
        # Collect all current group_ids
        current_group_ids = {row[0] for row in result.fetchall() if row[0] is not None}

        # Generate a unique UUID not in the current group_ids
        while True:
            new_group_id = str(uuid.uuid4())
            if new_group_id not in current_group_ids:
                return new_group_id


    async def get_layers_by_project(self, project_id: int):
        # Fetch all layers associated with a specific project
        result = await self.db.execute(
            select(models.Layer).filter(models.Layer.project_id == project_id)
        )
        layers = result.scalars().all()
        
        group_counter = {}
        all_layers = {}

        for layer in layers:

            if layer.group_id not in all_layers:
                all_layers[layer.group_id] = {
                    'name': layer.group_name,
                    'project_id': layer.project_id,
                    'layers': []
                }

                group_counter[layer.group_id] = []

            
            # Check if the layer's group exists in all_layers
            if layer.name not in group_counter[layer.group_id]:
                group_counter[layer.group_id].append(layer.name)
                all_layers[layer.group_id]['layers'].append({
                    "name": layer.name,  # You might have to ensure this is retrieved correctly
                    "data": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                        "id": layer.id,
                        "type": "Feature",
                        "geometry": serialize_geometry(layer.geometry),  # Ensure this is a valid GeoJSON
                        "properties": {
                            "big_flows": layer.big_flows,  # Adapt based on your model
                            "destination": layer.destination,  # Adapt based on your model
                            "destination_attr": layer.destination_attr,  # Adapt based on your model
                            "distance": layer.distance,  # Adapt based on your model
                            "flow": layer.flow,  # Adapt based on your model
                            "origin": layer.origin,  # Adapt based on your model
                            "origin_attr": layer.origin_attr,  # Adapt based on your model
                            "population": layer.population,  # Adapt based on your model
                            "scaled_flows_forvis": layer.scaled_flows_forvis,  # Adapt based on your model
                            "duration": layer.duration,
                            "in_out_diff":layer.in_out_diff,
                            "out_diff":layer.out_diff,
                            "in_diff":layer.in_diff,

                            "city_category":layer.city_category,

                            "factories_total":layer.factories_total,
                            "harsh_climate":layer.harsh_climate,
                            "migrations_from_each_city":layer.migrations_from_each_city,
                            "region_city":layer.region_city,
                            "ueqi_citywide_space":layer.ueqi_citywide_space,
                            "ueqi_green_spaces":layer.ueqi_green_spaces,

                            "ueqi_public_and_business_infrastructure":layer.ueqi_public_and_business_infrastructure,
                            "ueqi_residential":layer.ueqi_residential,
                            "ueqi_social_and_leisure_infrastructure":layer.ueqi_social_and_leisure_infrastructure,
                            "ueqi_street_networks":layer.ueqi_street_networks,
                            "median_salary":layer.median_salary,
                            'estimate':layer.estimate

                        }
                    }
                        ]
                    },
                    "style": layer.style  # Store the style directly here
                })

            else:
                for i in all_layers[layer.group_id]['layers']:
                    if layer.name == i['name']:
                        i['data']['features'].append(
                                    {
                                "id": layer.id,
                                "type": "Feature",
                                "geometry": serialize_geometry(layer.geometry),  # Ensure this is a valid GeoJSON
                                "properties": {
                                    "big_flows": layer.big_flows,  # Adapt based on your model
                                    "destination": layer.destination,  # Adapt based on your model
                                    "destination_attr": layer.destination_attr,  # Adapt based on your model
                                    "distance": layer.distance,  # Adapt based on your model
                                    "flow": layer.flow,  # Adapt based on your model
                                    "origin": layer.origin,  # Adapt based on your model
                                    "origin_attr": layer.origin_attr,  # Adapt based on your model
                                    "population": layer.population,  # Adapt based on your model
                                    "scaled_flows_forvis": layer.scaled_flows_forvis,  # Adapt based on your model
                                    "duration": layer.duration,
                                    "in_out_diff":layer.in_out_diff,
                                    "out_diff":layer.out_diff,
                                    "in_diff":layer.in_diff,
                                    "city_category":layer.city_category,

                                    "factories_total":layer.factories_total,
                                    "harsh_climate":layer.harsh_climate,
                                    "migrations_from_each_city":layer.migrations_from_each_city,
                                    "region_city":layer.region_city,
                                    "ueqi_citywide_space":layer.ueqi_citywide_space,
                                    "ueqi_green_spaces":layer.ueqi_green_spaces,

                                    "ueqi_public_and_business_infrastructure":layer.ueqi_public_and_business_infrastructure,
                                    "ueqi_residential":layer.ueqi_residential,
                                    "ueqi_social_and_leisure_infrastructure":layer.ueqi_social_and_leisure_infrastructure,
                                    "ueqi_street_networks":layer.ueqi_street_networks,
                                    "median_salary":layer.median_salary,
                                    'estimate':layer.estimate

                                }
                            }
                        )
                

            # Append layer data in GeoJSON format

            # for l in all_layers[layer.group_id]['layers']:
            #     l["data"]["features"].append(
            #     {
            #         "id": layer.id,
            #         "type": "Feature",
            #         "geometry": serialize_geometry(layer.geometry),  # Ensure this is a valid GeoJSON
            #         "properties": {
            #             "big_flows": layer.big_flows,  # Adapt based on your model
            #             "destination": layer.destination,  # Adapt based on your model
            #             "destination_attr": layer.destination_attr,  # Adapt based on your model
            #             "distance": layer.distance,  # Adapt based on your model
            #             "flow": layer.flow,  # Adapt based on your model
            #             "origin": layer.origin,  # Adapt based on your model
            #             "origin_attr": layer.origin_attr,  # Adapt based on your model
            #             "population": layer.population,  # Adapt based on your model
            #             "scaled_flows_forvis": layer.scaled_flows_forvis  # Adapt based on your model
            #         }
            #     }
            # )

        # Prepare the final response structure
        layers_response = []

        for _, group in all_layers.items():
            layers_response.append(group)
            # print('\n\n\n\n\n\n\n\n\n\n', group["style"])
            # layers_response.append({
            #     "name": group["name"],
            #     "data": group["data"],
            #     "style": {
            #         "fillOpacity": group["style"].get("fillOpacity", 1),   # Adjust these as per your style model
            #         "lineWidth": group["style"].get("lineWidth", 1),     
            #         "color": group["style"].get("color"),          # 
            #         'circleRadius': group['style'].get('circleRadius',1)
            #         # Adjust as per your model
            #     }
            # })

        return {
            "layer_groups": layers_response
        }
        
    async def create_project_with_layers(self, layers_data: dict):
        layers = []

        # Ensure project_id is provided
        project_id = layers_data.get("project_id")
        if project_id is None:
            raise ValueError("project_id must be provided")
        
        new_group_id = await self.generate_unique_group_id(project_id)
        print(f"Generated unique group_id: {new_group_id}")

        # Create a layer instance for each feature in the provided data
        for layer_data in layers_data.get("layers", []):
            if layer_data["data"]["type"] == "FeatureCollection":

                # print(layer_data, '\n\n\n\n\n\\n\n', layer_data["data"]["features"])
                for feature in layer_data["data"]["features"]:
                    f = feature.get('properties')
                    # Convert GeoJSON to Shapely geometry and then to WKT
                    geom = shape(feature["geometry"])
                    wkt_geometry = from_shape(geom, srid=4326)

                    # Create Layer object with robust handling for optional fields
                    layer = models.Layer(
                        project_id=project_id,  # Ensure project_id exists
                        group_name=layers_data.get('name'),  # Default if not present
                        geometry=wkt_geometry,
                        name=str(layer_data.get("name")),  # Use .get() for safety
                        style=layer_data.get("style", {}),  # Handle missing style dynamically
                        big_flows=f.get("big_flows"),  # Include big_flows if present
                        destination=f.get("destination"),  # Handle optional destination
                        duration=f.get("duration"),
                        destination_attr = f.get("destination_attr") if f.get("destination_attr") is not None else None,  # Handle optional
                        distance=f.get("distance"),  # Handle optional distance
                        flow=f.get("flow"),  # Handle optional flow
                        origin=f.get("origin"),  # Handle optional origin
                        origin_attr=f.get("origin_attr") if f.get("origin_attr") is not None else None,  # Handle optional origin_attr
                        population=f.get("population"),  # Handle optional population
                        scaled_flows_forvis=f.get("scaled_flows_forvis"),  # Handle optional scaled_flows_forvis
                        layer_mini_ids = await self.generate_unique_group_id(project_id),
                        group_id=new_group_id,
                        in_out_diff =f.get("in_out_diff"),
                        out_diff = f.get("out_diff"),
                        in_diff = f.get("in_diff"),

                        city_category = f.get("city_category"),

                        factories_total=f.get("factories_total"),
                        harsh_climate=f.get("harsh_climate"),
                        migrations_from_each_city=f.get("migrations_from_each_city"),
                        region_city=f.get("region_city"),
                        ueqi_citywide_space=f.get("ueqi_citywide_space"),
                        ueqi_green_spaces=f.get("ueqi_green_spaces"),

                        ueqi_public_and_business_infrastructure=f.get("ueqi_public_and_business_infrastructure"),
                        ueqi_residential=f.get("ueqi_residential"),
                        ueqi_social_and_leisure_infrastructure=f.get("ueqi_social_and_leisure_infrastructure"),
                        ueqi_street_networks=f.get("ueqi_street_networks"),

                        median_salary=f.get("median_salary"),
                        estimate=f.get("estimate")
                    )
                    layers.append(layer)

        # Store layers in the database
        self.db.add_all(layers)
        await self.db.commit()

        # Optionally, refresh each layer if your Layer model requires it for other fields (like IDs)
        for layer in layers:
            await self.db.refresh(layer)

        # Return a response with layer IDs and names
        return {"layers": [{"id": layer.id, "name": layer.name} for layer in layers]}

    
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

class SpecialistCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_specialists_by_project_id(self, project_id: int):
        """
        Fetch all specialists associated with a specific project.
        """
        stmt = (
            select(models.Specialist)
            .filter(models.Specialist.project_id == project_id)
        ).execution_options(autocommit=True)
        result = await self.db.execute(stmt)
        return result.scalars().all()