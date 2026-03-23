from datetime import date

from pydantic import BaseModel

from app.schemas.common import RiskIndicatorOut, SourceRecordOut


class SearchFacetSummary(BaseModel):
    audit_findings_count: int
    open_investigations_count: int
    anomaly_count: int


class EntitySearchItem(BaseModel):
    entity_id: str
    name: str
    entity_type: str
    state: str
    county: str
    city: str
    program_category: str
    total_awarded_amount: float
    summary: SearchFacetSummary
    indicators: list[RiskIndicatorOut]


class EntitySearchResponse(BaseModel):
    total: int
    items: list[EntitySearchItem]


class FindingOut(BaseModel):
    finding_id: str
    category: str
    status: str
    summary: str
    amount: float | None
    event_date: date
    source_ids: list[str]


class InvestigationOut(BaseModel):
    investigation_id: str
    status: str
    summary: str
    event_date: date
    source_ids: list[str]


class EntityDetailResponse(BaseModel):
    entity_id: str
    name: str
    entity_type: str
    state: str
    county: str
    city: str
    latitude: float
    longitude: float
    program_category: str
    total_awarded_amount: float
    audit_findings_count: int
    open_investigations_count: int
    anomaly_count: int
    indicators: list[RiskIndicatorOut]
    findings: list[FindingOut]
    investigations: list[InvestigationOut]
    sources: list[SourceRecordOut]
