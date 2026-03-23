from datetime import date

from pydantic import BaseModel, Field


class RawSourceDocument(BaseModel):
    source_name: str
    source_type: str
    state: str = "CA"
    program_category: str = "procurement"
    payload: dict


class NormalizedSourceRecord(BaseModel):
    external_id: str
    source_type: str
    publisher: str
    title: str
    publication_date: date | None = None
    url: str
    excerpt: str = ""


class NormalizedEntity(BaseModel):
    external_id: str
    name: str
    entity_type: str
    state_code: str = "CA"
    county_name: str | None = None
    city_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class NormalizedAward(BaseModel):
    external_id: str
    entity_external_id: str
    program_category: str = "procurement"
    award_number: str | None = None
    award_date: date | None = None
    awarded_amount: float | None = None
    awarding_agency: str | None = None


class NormalizedFinding(BaseModel):
    external_id: str
    entity_external_id: str
    status: str
    summary: str
    amount: float | None = None
    event_date: date | None = None
    source_external_id: str


class IndicatorInput(BaseModel):
    rule_key: str
    title: str
    description: str
    methodology: str
    severity: str = Field(pattern="^(low|medium|high)$")
    entity_external_id: str
    source_external_id: str | None = None
    evidence: list[dict] = Field(default_factory=list)
