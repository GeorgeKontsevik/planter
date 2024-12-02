# app/models.py

from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint
from api.app.enums import IndustryEnum, SpecialtyEnum

Base = declarative_base()

import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

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

    # Связь с таблицей specialists
    specialists = relationship("Specialist", back_populates="project", lazy="selectin", cascade="all, delete-orphan")


class Specialist(Base):
    __tablename__ = "specialists"
    
    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, primary_key=False, index=False, default=0)
    specialty = Column(String, unique=False, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (
        UniqueConstraint("specialty", "project_id", name="unique_specialist_project"),
    )
    project = relationship(
        "Project",
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
