from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app.routers import router
from api.app.core.config import settings


app = FastAPI(debug=settings.FASTAPI_DEBUG)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/factory_api")
