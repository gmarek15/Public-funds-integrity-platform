from app.domain.models import EntityRecord, IndicatorEvidence, RiskIndicator


class TransparentRiskEngine:
    """Builds explainable, source-backed indicators from public records."""

    def evaluate(self, entity: EntityRecord) -> list[RiskIndicator]:
        indicators: list[RiskIndicator] = []

        if entity.audit_findings_count > 0:
            indicators.append(
                RiskIndicator(
                    indicator_id=f"{entity.entity_id}:audit-findings",
                    indicator_key="audit_findings_present",
                    title="Confirmed audit findings are present",
                    severity="medium",
                    narrative=(
                        "Official audit records for this entity include confirmed findings. "
                        "This reflects published audit observations, not an accusation of fraud."
                    ),
                    methodology=(
                        "Triggered when one or more public audit findings are linked to the entity."
                    ),
                    evidence=[
                        IndicatorEvidence(
                            label="Confirmed audit findings",
                            value=str(entity.audit_findings_count),
                            source_ids=[
                                source.source_id
                                for source in entity.sources
                                if source.source_type == "audit_report"
                            ],
                        )
                    ],
                )
            )

        if entity.open_investigations_count > 0:
            indicators.append(
                RiskIndicator(
                    indicator_id=f"{entity.entity_id}:open-investigation",
                    indicator_key="open_investigation_notice",
                    title="Open investigation or administrative review notice",
                    severity="medium",
                    narrative=(
                        "A public record indicates an open investigation or administrative review. "
                        "Open status does not imply a final adverse determination."
                    ),
                    methodology=(
                        "Triggered when a linked source record identifies an investigation or review "
                        "with status marked open."
                    ),
                    evidence=[
                        IndicatorEvidence(
                            label="Open investigations",
                            value=str(entity.open_investigations_count),
                            source_ids=[
                                source.source_id
                                for source in entity.sources
                                if source.source_type == "investigation_notice"
                            ],
                        )
                    ],
                )
            )

        if entity.anomaly_count > 0:
            indicators.append(
                RiskIndicator(
                    indicator_id=f"{entity.entity_id}:spend-anomaly",
                    indicator_key="spend_pattern_anomaly",
                    title="Automated spending pattern anomaly",
                    severity="low",
                    narrative=(
                        "Automated checks flagged spending patterns that merit review against normal "
                        "procurement behavior. This is a heuristic indicator, not a confirmed finding."
                    ),
                    methodology=(
                        "Triggered when rule-based analytics detect unusual payment timing, concentration, "
                        "or repeat contract patterns in public spending data."
                    ),
                    evidence=[
                        IndicatorEvidence(
                            label="Anomaly rules triggered",
                            value=str(entity.anomaly_count),
                            source_ids=[
                                source.source_id
                                for source in entity.sources
                                if source.source_type == "spending_record"
                            ],
                        )
                    ],
                )
            )

        return indicators
