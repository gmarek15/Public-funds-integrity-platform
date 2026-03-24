from app.repositories.washington_open_checkbook import WashingtonOpenCheckbookRepository
from app.services.entities import EntityService

_repository = WashingtonOpenCheckbookRepository()
_service = EntityService(repository=_repository)


def get_entity_service() -> EntityService:
    return _service
