from datetime import date

from pydantic import BaseModel, ConfigDict


class SourceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_id: str
    source_type: str
    publisher: str
    title: str
    publication_date: date
    url: str
    excerpt: str


class EvidenceOut(BaseModel):
    label: str
    value: str
    source_ids: list[str]


class RiskIndicatorOut(BaseModel):
    indicator_id: str
    indicator_key: str
    title: str
    severity: str
    narrative: str
    methodology: str
    evidence: list[EvidenceOut]
