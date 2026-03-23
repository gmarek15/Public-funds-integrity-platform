from abc import ABC, abstractmethod

from app.domain.models import EntityRecord


class EntityRepository(ABC):
    @abstractmethod
    def list_entities(self, state: str, program_category: str) -> list[EntityRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_entity(self, entity_id: str) -> EntityRecord | None:
        raise NotImplementedError
