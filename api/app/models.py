# app/models.py

from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from api.app.enums import IndustryEnum, SpecialtyEnum

Base = declarative_base()

import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

# Association table for many-to-many relationship with count
project_specialist_table = Table(
    "project_specialists",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("specialist_id", Integer, ForeignKey("specialists.id", ondelete="CASCADE"), primary_key=True),
    Column("count", Integer, nullable=False, default=0)  # Number of specialists per project
)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Default Project Name", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    # specialties = Column(JSON, nullable=False)  # Список из Enum
    industry_name = Column(String, nullable=True)  # Дополнительное название индустрии
    n_hours = Column(Integer, default=0, nullable=True)  # Дополнительное поле часов

    # Геометрия
    geometry = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    
    # Связи
    layers = relationship(
        "Layer",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True, lazy="selectin"
    )
    data = relationship("Data", back_populates="project", cascade="all, delete-orphan", lazy="selectin")

    # Связь с таблицей specialists
    specialists = relationship("Specialist", back_populates="project", lazy="selectin", secondary=project_specialist_table)

class Specialist(Base):
    __tablename__ = "specialists"
    
    id = Column(Integer, primary_key=True, index=True)
    specialty = Column(String, unique=True, nullable=False)
    project = relationship(
        "Project",
        secondary=project_specialist_table,
        back_populates="specialists"
    )

class Layer(Base):
    __tablename__ = "layers"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    geometry = Column(Geometry(geometry_type='GEOMETRY', srid=4326), nullable=False)
    properties = Column(JSON, nullable=True)  # Дополнительные свойства слоя

    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    # Связи
    project = relationship("Project", back_populates="layers")

class Data(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    # Связи
    project = relationship("Project", back_populates="data")