from pfip_etl.models import (
    IndicatorInput,
    NormalizedAward,
    NormalizedEntity,
    NormalizedSourceRecord,
    RawSourceDocument,
)


def normalize_procurement_documents(
    documents: list[RawSourceDocument],
) -> tuple[list[NormalizedSourceRecord], list[NormalizedEntity], list[NormalizedAward], list[IndicatorInput]]:
    sources: list[NormalizedSourceRecord] = []
    entities: list[NormalizedEntity] = []
    awards: list[NormalizedAward] = []
    indicators: list[IndicatorInput] = []

    for document in documents:
        for record in document.payload.get("records", []):
            source_external_id = record["source_external_id"]
            entity_external_id = record["entity_external_id"]

            sources.append(
                NormalizedSourceRecord(
                    external_id=source_external_id,
                    source_type=document.source_type,
                    publisher="California Open Checkbook",
                    title="California procurement seed records",
                    url="https://example.gov/spending/fy2026",
                    excerpt="Seed spending record used for initial pipeline development.",
                )
            )
            entities.append(
                NormalizedEntity(
                    external_id=entity_external_id,
                    name=record["entity_name"],
                    entity_type="vendor",
                    city_name=record.get("city_name"),
                    county_name=record.get("county_name"),
                )
            )
            awards.append(
                NormalizedAward(
                    external_id=f"award:{entity_external_id}:{source_external_id}",
                    entity_external_id=entity_external_id,
                    awarded_amount=record.get("awarded_amount"),
                    awarding_agency=record.get("awarding_agency"),
                )
            )
            indicators.append(
                IndicatorInput(
                    rule_key="spend_pattern_anomaly",
                    title="Automated spending pattern anomaly",
                    description="Flags payment timing or concentration patterns for review.",
                    methodology="Prototype rule emits a low-severity anomaly for seeded outlier test records.",
                    severity="low",
                    entity_external_id=entity_external_id,
                    source_external_id=source_external_id,
                    evidence=[{"label": "seed_record", "value": "true"}],
                )
            )

    return sources, entities, awards, indicators
