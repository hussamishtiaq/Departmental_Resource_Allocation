from fastapi import APIRouter

from app.api.v1.endpoints import auth, departments, reports, reservations, resources, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(resources.router)
api_router.include_router(reservations.router)
api_router.include_router(reports.router)
api_router.include_router(reservations.router)
