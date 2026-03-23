from app.repositories.sample_data import SampleEntityRepository
from app.services.entities import EntityService

_repository = SampleEntityRepository()
_service = EntityService(repository=_repository)


def get_entity_service() -> EntityService:
    return _service
