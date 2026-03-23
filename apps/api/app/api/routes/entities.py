from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_entity_service
from app.schemas.entity import EntityDetailResponse
from app.services.entities import EntityService

router = APIRouter()


@router.get("/entities/{entity_id}", response_model=EntityDetailResponse)
def get_entity(
    entity_id: str,
    service: EntityService = Depends(get_entity_service),
) -> EntityDetailResponse:
    entity = service.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity
