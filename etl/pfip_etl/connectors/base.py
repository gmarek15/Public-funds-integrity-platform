from abc import ABC, abstractmethod

from pfip_etl.models import RawSourceDocument


class SourceConnector(ABC):
    @abstractmethod
    def fetch(self) -> list[RawSourceDocument]:
        raise NotImplementedError
