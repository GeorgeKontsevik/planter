# app/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint
import uuid
import logging

Base = declarative_base()

# Log SQLAlchemy queries for debugging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Default Project Name", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    # Additional project attributes
    industry_name = Column(String, nullable=True)
    n_hours = Column(Float, default=0, nullable=True)
    workforce_type = Column(String, nullable=True)
    specialists_total = Column(Integer, nullable=True)
    graduates_total = Column(Integer, nullable=True)
    all_total = Column(Integer, nullable=True)
    metric_bool = Column(Boolean, nullable=True)
    metric_float = Column(Float, nullable=True)

    # Geometry attribute as a Point
    geometry = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)

    # Relationships
    layers = relationship(
        "Layer",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )
    
    specialists = relationship(
        "Specialist",
        back_populates="project",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class Specialist(Base):
    __tablename__ = "specialists"

    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, default=0, nullable=False)
    specialty = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
   
    __table_args__ = (
        UniqueConstraint("specialty", "project_id", name="unique_specialist_project"),
    )
    
    project = relationship(
        "Project",
        back_populates="specialists"
    )

class Layer(Base):
    __tablename__ = 'layers'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    group_id = Column(String, nullable=False)
    group_name = Column(String, nullable=False)
    name = Column(String, nullable=True)
    geometry = Column(Geometry, nullable=False)  # Ensure geometry is required
    style = Column(JSON, nullable=True)
    specialists_data=Column(JSON, nullable=True)
    big_flows = Column(JSON, nullable=True)  # Allow for big_flows JSON data
    destination = Column(String, nullable=True)  # Adapt based on your model
    destination_attr = Column(Integer, nullable=True)  # Adapt based on your model
    distance = Column(Integer, nullable=True)  # Adapt based on your model
    flow = Column(Integer, nullable=True)  # Adapt based on your model
    origin = Column(String, nullable=True)  # Adapt based on your model
    origin_attr = Column(Integer, nullable=True)  # Adapt based on your model
    population = Column(Integer, nullable=True)  # Adapt based on your model
    scaled_flows_forvis = Column(JSON, nullable=True)  # Adapt based on your model
    layer_mini_ids = Column(String, nullable=False)
    duration=Column(Float, nullable=True)
    in_diff=Column(Integer, nullable=True)
    out_diff=Column(Integer, nullable=True)
    in_out_diff=Column(Integer, nullable=True)

    city_category = Column(String,nullable=True)
    factories_total=Column(Integer,nullable=True)
    harsh_climate=Column(Integer,nullable=True)
    migrations_from_each_city=Column(Float,nullable=True)
    region_city=Column(String,nullable=True)
    ueqi_citywide_space=Column(Integer,nullable=True)
    ueqi_green_spaces=Column(Integer,nullable=True)
    ueqi_public_and_business_infrastructure=Column(Integer,nullable=True)
    ueqi_residential=Column(Integer,nullable=True)
    ueqi_social_and_leisure_infrastructure=Column(Integer,nullable=True)
    ueqi_street_networks=Column(Integer,nullable=True)
    median_salary=Column(Integer, nullable=True)
    estimate=Column(Float, nullable=True)
    hours=Column(Float, nullable=True)

    

    def __init__(self, project_id, group_id=None, name=None, geometry=None, style=None, 
                 group_name=None, big_flows=None, destination=None, destination_attr=None, 
                 distance=None, flow=None, origin=None, origin_attr=None, population=None, 
                 scaled_flows_forvis=None, layer_mini_ids=None, duration=None, in_diff=None, out_diff=None,in_out_diff=None,
                 city_category=None,factories_total=None,harsh_climate=None,migrations_from_each_city=None,region_city=None,ueqi_citywide_space=None,ueqi_green_spaces=None, ueqi_public_and_business_infrastructure=None,ueqi_residential=None,ueqi_social_and_leisure_infrastructure=None,ueqi_street_networks=None,
                 median_salary=None, estimate=None,specialists_data=None,
                 hours=None
                 ):
        
        self.project_id = project_id
        self.group_id = group_id
        self.layer_mini_ids = layer_mini_ids
        self.name = name
        self.geometry = geometry
        self.style = style
        self.group_name = group_name
        self.big_flows = big_flows  # Initialize big_flows
        self.destination = destination  # Set destination
        self.destination_attr = destination_attr  # Set destination_attr
        self.distance = distance  # Set distance
        self.flow = flow  # Set flow
        self.origin = origin  # Set origin
        self.origin_attr = origin_attr  # Set origin_attr
        self.population = population  # Set population
        self.scaled_flows_forvis = scaled_flows_forvis  # Set scaled flows
        self.in_diff = in_diff
        self.out_diff=out_diff
        self.duration = duration
        self.in_out_diff=in_out_diff
        self.city_category = city_category
        self.factories_total=factories_total
        self.harsh_climate=harsh_climate
        self.migrations_from_each_city=migrations_from_each_city
        self.region_city=region_city
        self.ueqi_citywide_space=ueqi_citywide_space
        self.ueqi_green_spaces=ueqi_green_spaces
        self.ueqi_public_and_business_infrastructure=ueqi_public_and_business_infrastructure
        self.ueqi_residential=ueqi_residential
        self.ueqi_social_and_leisure_infrastructure=ueqi_social_and_leisure_infrastructure
        self.ueqi_street_networks=ueqi_street_networks

        self.median_salary=median_salary
        self.estimate=estimate
        self.specialists_data=specialists_data

        self.hours=hours
    # Define the relationship with Project
    project = relationship("Project", back_populates="layers")
