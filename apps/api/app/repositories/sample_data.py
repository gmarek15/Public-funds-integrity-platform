from datetime import date

from app.domain.models import EntityRecord, FindingRecord, InvestigationRecord, SourceRecord
from app.repositories.base import EntityRepository


class SampleEntityRepository(EntityRepository):
    def __init__(self) -> None:
        self._entities = {
            entity.entity_id: entity
            for entity in [
                EntityRecord(
                    entity_id="entity-ca-oak-001",
                    name="Civic Bridge Consulting LLC",
                    entity_type="vendor",
                    state="CA",
                    county="Alameda",
                    city="Oakland",
                    latitude=37.8044,
                    longitude=-122.2712,
                    program_category="procurement",
                    total_awarded_amount=2450000.00,
                    audit_findings_count=2,
                    open_investigations_count=1,
                    anomaly_count=2,
                    sources=[
                        SourceRecord(
                            source_id="src-audit-2025-001",
                            source_type="audit_report",
                            publisher="California State Auditor",
                            title="Procurement Controls Review - Oakland Infrastructure Services",
                            publication_date=date(2025, 8, 12),
                            url="https://example.gov/audits/oakland-procurement-2025",
                            excerpt="The audit identified documentation gaps and exceptions to competitive bidding procedures.",
                        ),
                        SourceRecord(
                            source_id="src-enforcement-2026-003",
                            source_type="investigation_notice",
                            publisher="County Inspector General",
                            title="Public notice of open review into contract administration practices",
                            publication_date=date(2026, 1, 18),
                            url="https://example.gov/notices/contract-admin-review",
                            excerpt="The notice states the review is ongoing and does not announce a final determination.",
                        ),
                        SourceRecord(
                            source_id="src-spend-2026-010",
                            source_type="spending_record",
                            publisher="California Open Checkbook",
                            title="State procurement disbursement records FY2026",
                            publication_date=date(2026, 2, 10),
                            url="https://example.gov/spending/fy2026",
                            excerpt="Disbursement records show accelerated payment timing across three related contracts.",
                        ),
                    ],
                    findings=[
                        FindingRecord(
                            finding_id="finding-001",
                            category="audit_finding",
                            status="confirmed",
                            summary="Audit report documented unsupported sole-source justification in sampled contracts.",
                            amount=320000.00,
                            event_date=date(2025, 8, 12),
                            source_ids=["src-audit-2025-001"],
                        ),
                        FindingRecord(
                            finding_id="finding-002",
                            category="audit_finding",
                            status="confirmed",
                            summary="Audit report found incomplete vendor performance documentation.",
                            amount=None,
                            event_date=date(2025, 8, 12),
                            source_ids=["src-audit-2025-001"],
                        ),
                    ],
                    investigations=[
                        InvestigationRecord(
                            investigation_id="inv-001",
                            status="open",
                            summary="Open administrative review into contract administration practices.",
                            event_date=date(2026, 1, 18),
                            source_ids=["src-enforcement-2026-003"],
                        ),
                    ],
                ),
                EntityRecord(
                    entity_id="entity-ca-sac-002",
                    name="Delta Regional Supply Co.",
                    entity_type="vendor",
                    state="CA",
                    county="Sacramento",
                    city="Sacramento",
                    latitude=38.5816,
                    longitude=-121.4944,
                    program_category="procurement",
                    total_awarded_amount=1180000.00,
                    audit_findings_count=0,
                    open_investigations_count=0,
                    anomaly_count=1,
                    sources=[
                        SourceRecord(
                            source_id="src-spend-2026-010",
                            source_type="spending_record",
                            publisher="California Open Checkbook",
                            title="State procurement disbursement records FY2026",
                            publication_date=date(2026, 2, 10),
                            url="https://example.gov/spending/fy2026",
                            excerpt="Disbursement records show accelerated payment timing across three related contracts.",
                        ),
                    ],
                    findings=[],
                    investigations=[],
                ),
            ]
        }

    def list_entities(self, state: str, program_category: str) -> list[EntityRecord]:
        return [
            entity
            for entity in self._entities.values()
            if entity.state.lower() == state.lower()
            and entity.program_category.lower() == program_category.lower()
        ]

    def get_entity(self, entity_id: str) -> EntityRecord | None:
        return self._entities.get(entity_id)
