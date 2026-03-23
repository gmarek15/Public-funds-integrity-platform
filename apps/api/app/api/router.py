from fastapi import APIRouter

from app.api.routes import entities, health, map_view, search

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(entities.router, tags=["entities"])
api_router.include_router(map_view.router, tags=["map"])
