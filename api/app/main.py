# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .routers import closest, city, projects, layers
from .database import engine, get_db
from . import models, schemas, crud

from sqlalchemy.ext.asyncio import AsyncSession

import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

app = FastAPI(
    title="API for Factory Location Service",
    description="API for getting an estimate of factory location based on available workforce.",
    version="0.1.0",
    debug=True,  # Consider setting this via your settings/config
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(closest.router, prefix="/factory_api", tags=["Closest"])
app.include_router(city.router, prefix="/factory_api", tags=["City"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(layers.router, prefix="/layers", tags=["Layers"])

import logging
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# Initialize database tables on startup
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

# --- Metrics Endpoint ---

@app.post("/metrics/", response_model=schemas.MetricsResponse, tags=["Metrics"])
async def calculate_metrics(request: schemas.MetricsRequest):
    # Replace with your actual metrics calculation logic
    metric1 = request.parameter1 * 2
    metric2 = request.parameter2 + 100
    return schemas.MetricsResponse(metric1=metric1, metric2=metric2)

# --- CRUD Endpoints for Data ---

@app.post(
    "/data/",
    response_model=schemas.DataRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Data"],
)
async def create_data(
    data: schemas.DataCreate, db: AsyncSession = Depends(get_db)
):
    return await crud.create_data(db, data)

@app.get("/data/{data_id}", response_model=schemas.DataRead, tags=["Data"])
async def read_data(data_id: int, db: AsyncSession = Depends(get_db)):
    db_data = await crud.get_data(db, data_id)
    if db_data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    return db_data

@app.put("/data/{data_id}", response_model=schemas.DataRead, tags=["Data"])
async def update_existing_data(
    data_id: int, data: schemas.DataUpdate, db: AsyncSession = Depends(get_db)
):
    db_data = await crud.update_data(db, data_id, data)
    if db_data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    return db_data

@app.delete("/data/{data_id}", response_model=schemas.DataRead, tags=["Data"])
async def delete_data(data_id: int, db: AsyncSession = Depends(get_db)):
    db_data = await crud.delete_data(db, data_id)
    if db_data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    return db_data

@app.get("/data/", response_model=List[schemas.DataRead], tags=["Data"])
async def list_data(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    data = await crud.list_data(db, skip=skip, limit=limit)
    return data