from datetime import date, datetime

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


class SourceRunManifest(BaseModel):
    state_code: str
    source_slug: str
    source_url: str
    local_path: str
    retrieved_at: datetime
    sha256: str


class PaymentRawRecord(BaseModel):
    state_code: str
    source_slug: str
    biennium: str
    fiscal_year: int
    fiscal_month: int
    agency_code: str
    agency_name: str
    object_code: str
    category_name: str
    subobject_code: str
    subcategory_name: str
    vendor_name_raw: str
    amount: float
    source_url: str
    source_sheet: str
    source_row_number: int
    retrieved_at: datetime
    source_file_sha256: str
