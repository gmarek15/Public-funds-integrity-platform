from fastapi import APIRouter, Depends, Query

from app.dependencies import get_entity_service
from app.schemas.map import EntityMapResponse
from app.services.entities import EntityService

router = APIRouter()


@router.get("/map/entities", response_model=EntityMapResponse)
def get_entity_map(
    state: str = Query(default="CA"),
    program_category: str = Query(default="procurement"),
    service: EntityService = Depends(get_entity_service),
) -> EntityMapResponse:
    return service.get_map(state=state, program_category=program_category)
