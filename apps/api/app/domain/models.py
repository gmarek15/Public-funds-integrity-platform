from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class SourceRecord:
    source_id: str
    source_type: str
    publisher: str
    title: str
    publication_date: date
    url: str
    excerpt: str


@dataclass(slots=True)
class FindingRecord:
    finding_id: str
    category: str
    status: str
    summary: str
    amount: float | None
    event_date: date
    source_ids: list[str]


@dataclass(slots=True)
class InvestigationRecord:
    investigation_id: str
    status: str
    summary: str
    event_date: date
    source_ids: list[str]


@dataclass(slots=True)
class IndicatorEvidence:
    label: str
    value: str
    source_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RiskIndicator:
    indicator_id: str
    indicator_key: str
    title: str
    severity: str
    narrative: str
    methodology: str
    evidence: list[IndicatorEvidence]


@dataclass(slots=True)
class EntityRecord:
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
    sources: list[SourceRecord]
    findings: list[FindingRecord]
    investigations: list[InvestigationRecord]
