from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.auth_service import seed_roles
from app.services.department_service import get_or_create_department


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Make sure the roles and the single department exist (idempotent). Requires migrations applied.
    with SessionLocal() as db:
        seed_roles(db)
        get_or_create_department(db)
    yield


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {"message": "Department Resource Management API"}


@app.get("/health")
def health():
    return {"status": "ok"}
