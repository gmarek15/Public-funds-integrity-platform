from fastapi import APIRouter, Depends, Query

from app.dependencies import get_entity_service
from app.schemas.entity import EntitySearchResponse
from app.services.entities import EntityService

router = APIRouter()


@router.get("/search/entities", response_model=EntitySearchResponse)
def search_entities(
    q: str = Query(default="", description="Free-text query"),
    state: str = Query(default="WA"),
    program_category: str = Query(default="all"),
    limit: int = Query(default=20, ge=1, le=100),
    service: EntityService = Depends(get_entity_service),
) -> EntitySearchResponse:
    return service.search_entities(
        query=q,
        state=state,
        program_category=program_category,
        limit=limit,
    )
