from fastapi import APIRouter, Depends, Query

from app.dependencies import get_entity_service
from app.schemas.map import GeoOverviewResponse
from app.services.entities import EntityService

router = APIRouter()


@router.get("/map/entities", response_model=GeoOverviewResponse)
def get_entity_map(
    state: str = Query(default="WA"),
    program_category: str = Query(default="all"),
    service: EntityService = Depends(get_entity_service),
) -> GeoOverviewResponse:
    return service.get_map(state=state, program_category=program_category)
