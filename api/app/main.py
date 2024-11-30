# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .routers import closest, city, projects, layers
from .database import engine, get_db
from . import models, schemas, crud

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse



import logging
logging.basicConfig()

logger = logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

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
app.include_router(projects.router, prefix="/factory_api", tags=["Projects"])
app.include_router(layers.router, prefix="/factory_api", tags=["Layers"])




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
