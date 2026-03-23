from datetime import date

from pfip_etl.connectors.base import SourceConnector
from pfip_etl.models import RawSourceDocument


class CaliforniaProcurementConnector(SourceConnector):
    """Placeholder connector for the first California procurement source."""

    def fetch(self) -> list[RawSourceDocument]:
        return [
            RawSourceDocument(
                source_name="california_procurement_seed",
                source_type="spending_record",
                payload={
                    "generated_on": date(2026, 3, 1).isoformat(),
                    "records": [
                        {
                            "source_external_id": "spend-2026-010",
                            "entity_external_id": "vendor-001",
                            "entity_name": "Civic Bridge Consulting LLC",
                            "city_name": "Oakland",
                            "county_name": "Alameda",
                            "awarded_amount": 2450000.00,
                            "awarding_agency": "Oakland Infrastructure Services",
                        }
                    ],
                },
            )
        ]
