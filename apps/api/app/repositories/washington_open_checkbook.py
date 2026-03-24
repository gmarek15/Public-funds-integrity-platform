from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

from app.domain.models import EntityRecord, SourceRecord
from app.repositories.base import EntityRepository

OPEN_CHECKBOOK_URL = "https://www.fiscal.wa.gov/Spending/Checkbook"
OPEN_CHECKBOOK_OVERVIEW_URL = "https://fiscal.wa.gov/default/PublicationsAndReports/Spending/Checkbook"
OPEN_CHECKBOOK_DISCLAIMER_URL = "https://fiscal.wa.gov/Spending/DisclaimerWAVendorCB.pdf"
CMS_NPI_URL = "https://npiregistry.cms.hhs.gov/api-page"
DOH_PROVIDER_URL = "https://doh.wa.gov/licenses-permits-and-certificates/provider-credential-search"
DCYF_CHILD_CARE_URL = "https://www.dcyf.wa.gov/services/earlylearning-childcare/child-care-check"
DCYF_FINDER_URL = "https://www.findchildcarewa.org/"


@dataclass(slots=True)
class GeoOverviewRecord:
    features: list[dict[str, object]]
    city_summaries: list[dict[str, object]]
    cluster_summaries: list[dict[str, object]]
    reviews: list[dict[str, object]]
    metadata: dict[str, object]


class WashingtonOpenCheckbookRepository(EntityRepository):
    def __init__(self) -> None:
        dataset = self._load_dataset()
        self._entities = dataset["entities"]
        self._geo_overview = dataset["geo_overview"]

    def list_entities(self, state: str, program_category: str) -> list[EntityRecord]:
        if state.lower() != "wa":
            return []
        entities = list(self._entities.values())
        if program_category and program_category.lower() != "all":
            entities = [
                entity
                for entity in entities
                if entity.program_category.lower() == program_category.lower()
            ]
        return sorted(entities, key=lambda entity: entity.total_awarded_amount, reverse=True)

    def get_entity(self, entity_id: str) -> EntityRecord | None:
        return self._entities.get(entity_id)

    def get_geo_overview(self, state: str, program_category: str) -> dict[str, object]:
        if state.lower() != "wa":
            return {
                "type": "FeatureCollection",
                "features": [],
                "city_summaries": [],
                "county_summaries": [],
                "cluster_summaries": [],
                "reviews": [],
                "county_shapes": {
                    "state_code": state.upper(),
                    "source_url": "",
                    "view_box": "0 0 1000 620",
                    "bounds": {"min_lon": 0.0, "max_lon": 0.0, "min_lat": 0.0, "max_lat": 0.0},
                    "counties": [],
                },
                "metadata": {"state_code": state.upper(), "program_category": program_category},
            }

        if not program_category or program_category.lower() == "all":
            return self._geo_overview

        allowed_features = [
            feature
            for feature in self._geo_overview["features"]
            if feature["properties"]["program_category"].lower() == program_category.lower()
        ]
        allowed_reviews = [
            review
            for review in self._geo_overview["reviews"]
            if program_category.lower() in review["focus_areas"].lower()
        ]
        allowed_clusters = [
            cluster
            for cluster in self._geo_overview["cluster_summaries"]
            if program_category.lower() in cluster["focus_areas"].lower()
        ]
        allowed_cities = [
            city
            for city in self._geo_overview["city_summaries"]
            if program_category.lower() in city["focus_areas"].lower()
        ]
        return {
            "type": "FeatureCollection",
            "features": allowed_features,
            "city_summaries": allowed_cities,
            "county_summaries": [
                county
                for county in self._geo_overview["county_summaries"]
                if program_category.lower() in county["focus_areas"].lower()
            ],
            "cluster_summaries": allowed_clusters,
            "reviews": allowed_reviews,
            "county_shapes": self._geo_overview["county_shapes"],
            "metadata": self._geo_overview["metadata"] | {"program_category": program_category},
        }

    @staticmethod
    def _repo_root() -> Path:
        return Path(__file__).resolve().parents[4]

    @classmethod
    def _data_dir(cls) -> Path:
        return cls._repo_root() / "data" / "normalized" / "wa" / "open_checkbook"

    @classmethod
    def _read_csv(cls, name: str) -> list[dict[str, str]]:
        path = cls._data_dir() / name
        with path.open(encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    @classmethod
    def _file_date(cls, name: str) -> date:
        modified = (cls._data_dir() / name).stat().st_mtime
        return datetime.fromtimestamp(modified).date()

    @classmethod
    @lru_cache(maxsize=1)
    def _load_dataset(cls) -> dict[str, object]:
        identifier_rows = cls._read_csv("recipient_identifier_links.csv")
        geo_point_rows = cls._read_csv("recipient_geo_points.csv")
        city_summary_rows = cls._read_csv("recipient_geo_city_summary.csv")
        county_summary_rows = cls._read_csv("recipient_geo_county_summary.csv")
        cluster_summary_rows = cls._read_csv("recipient_geo_cluster_summary.csv")
        review_rows = cls._read_csv("recipient_colocation_reviews.csv")
        county_shapes = json.loads(
            (cls._data_dir() / "washington_county_shapes.json").read_text(encoding="utf-8")
        )

        geo_points_by_entity = {
            row["canonical_recipient_id"]: row
            for row in geo_point_rows
            if row["geocode_status"] == "matched"
        }
        review_by_cluster = {row["cluster_id"]: row for row in review_rows}

        grouped_identifiers: dict[str, list[dict[str, str]]] = {}
        for row in identifier_rows:
            if row["link_status"] != "verified":
                continue
            grouped_identifiers.setdefault(row["canonical_recipient_id"], []).append(row)

        entities: dict[str, EntityRecord] = {}
        for entity_id, rows in grouped_identifiers.items():
            ranked_rows = sorted(rows, key=lambda row: float(row["total_amount"]), reverse=True)
            anchor = geo_points_by_entity.get(entity_id, ranked_rows[0])
            review = review_by_cluster.get(anchor.get("proximity_cluster_id", ""))
            sources = cls._build_sources(entity_id=entity_id, anchor=anchor, review=review)
            entities[entity_id] = EntityRecord(
                entity_id=entity_id,
                name=anchor.get("canonical_recipient_name") or anchor["identifier_display"],
                entity_type=cls._entity_type(anchor["source_system"]),
                state=anchor["state_code"],
                county=anchor.get("county_name", "") or "Not yet derived",
                city=anchor.get("city", "") or "Statewide",
                zip_code=anchor.get("zip_code", ""),
                latitude=float(anchor.get("latitude") or 0),
                longitude=float(anchor.get("longitude") or 0),
                source_system=anchor["source_system"],
                program_category=anchor["primary_focus_area"],
                total_awarded_amount=float(anchor["total_amount"]),
                audit_findings_count=0,
                open_investigations_count=0,
                anomaly_count=1 if review else 0,
                sources=sources,
                findings=[],
                investigations=[],
            )

        features = []
        for row in geo_point_rows:
            if row["geocode_status"] != "matched":
                continue
            entity = entities.get(row["canonical_recipient_id"])
            if entity is None:
                continue
            cluster_id = row["proximity_cluster_id"]
            review = review_by_cluster.get(cluster_id)
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(row["longitude"]), float(row["latitude"])],
                    },
                    "properties": {
                        "entity_id": row["canonical_recipient_id"],
                        "name": entity.name,
                        "city": row["city"],
                        "state": row["state"],
                        "zip_code": row["zip_code"],
                        "county_name": row.get("county_name", ""),
                        "county_fips": row.get("county_fips", ""),
                        "program_category": row["primary_focus_area"],
                        "source_system": row["source_system"],
                        "total_amount": float(row["total_amount"]),
                        "payment_count": int(row["payment_count"]),
                        "anomaly_count": entity.anomaly_count,
                        "cluster_id": cluster_id,
                        "review_status": review["review_status"] if review else "",
                    },
                }
            )

        geo_overview = {
            "type": "FeatureCollection",
            "features": features,
            "city_summaries": [cls._normalize_city_summary(row) for row in city_summary_rows],
            "county_summaries": [cls._normalize_county_summary(row) for row in county_summary_rows],
            "cluster_summaries": [cls._normalize_cluster_summary(row) for row in cluster_summary_rows],
            "reviews": [cls._normalize_review(row) for row in review_rows],
            "county_shapes": county_shapes,
            "metadata": {
                "state_code": "WA",
                "program_category": "all",
                "data_sources": [
                    "Washington Open Checkbook",
                    "CMS NPI Registry",
                    "DCYF Child Care Check",
                    "U.S. Census Geocoder",
                ],
                "methodology_note": (
                    "Map layers are built from verified provider or facility identifiers and public "
                    "spending records. Co-location reviews are automated prompts for further review."
                ),
            },
        }

        return {"entities": entities, "geo_overview": geo_overview}

    @classmethod
    def _build_sources(
        cls,
        entity_id: str,
        anchor: dict[str, str],
        review: dict[str, str] | None,
    ) -> list[SourceRecord]:
        snapshot_date = cls._file_date("recipient_identifier_links.csv")
        source_records = [
            SourceRecord(
                source_id=f"{entity_id}:open-checkbook",
                source_type="spending_record",
                publisher="Washington State Fiscal Information",
                title="Washington Open Checkbook vendor payment records",
                publication_date=snapshot_date,
                url=OPEN_CHECKBOOK_URL,
                excerpt=(
                    f"Recipient-linked payment total in current Washington snapshot: "
                    f"${float(anchor['total_amount']):,.2f} across {int(anchor['payment_count'])} payments."
                ),
            ),
            SourceRecord(
                source_id=f"{entity_id}:open-checkbook-method",
                source_type="source_methodology",
                publisher="Washington State Fiscal Information",
                title="Washington Open Checkbook overview and disclosure notes",
                publication_date=cls._file_date("recipient_geo_summary.json")
                if (cls._data_dir() / "recipient_geo_summary.json").exists()
                else snapshot_date,
                url=OPEN_CHECKBOOK_OVERVIEW_URL,
                excerpt=(
                    "Washington publishes Open Checkbook spending data from its fiscal systems. "
                    "Coverage and exclusions should be reviewed before drawing conclusions."
                ),
            ),
            SourceRecord(
                source_id=f"{entity_id}:open-checkbook-disclaimer",
                source_type="source_methodology",
                publisher="Washington State Fiscal Information",
                title="Washington Open Checkbook disclaimer",
                publication_date=snapshot_date,
                url=OPEN_CHECKBOOK_DISCLAIMER_URL,
                excerpt=(
                    "The official disclaimer notes coverage limits and says the published payment data "
                    "should not be treated as audited findings."
                ),
            ),
        ]

        primary_url = anchor.get("source_url_primary", "")
        secondary_url = anchor.get("source_url_secondary", "")
        if primary_url:
            source_records.append(
                SourceRecord(
                    source_id=f"{entity_id}:identifier-primary",
                    source_type="identifier_registry",
                    publisher=cls._publisher(anchor["source_system"]),
                    title=cls._source_title(anchor["source_system"]),
                    publication_date=snapshot_date,
                    url=primary_url,
                    excerpt=anchor["linkage_explanation"]
                    if "linkage_explanation" in anchor
                    else (
                        f"Verified identifier source for {anchor['source_record_name']} via "
                        f"{anchor['source_system']}."
                    ),
                )
            )
        if secondary_url:
            source_records.append(
                SourceRecord(
                    source_id=f"{entity_id}:identifier-secondary",
                    source_type="identifier_registry",
                    publisher=cls._secondary_publisher(anchor["source_system"]),
                    title=cls._secondary_source_title(anchor["source_system"]),
                    publication_date=snapshot_date,
                    url=secondary_url,
                    excerpt=(
                        "Secondary official source used to corroborate identifier type, facility context, "
                        "or licensing context for this recipient."
                    ),
                )
            )
        if review:
            source_records.append(
                SourceRecord(
                    source_id=f"{entity_id}:colocation-review",
                    source_type="automated_review",
                    publisher="Public Funds Integrity Platform",
                    title="Automated co-location review prompt",
                    publication_date=cls._file_date("recipient_colocation_reviews.csv"),
                    url=OPEN_CHECKBOOK_URL,
                    excerpt=review["rationale"],
                )
            )
        return source_records

    @staticmethod
    def _entity_type(source_system: str) -> str:
        mapping = {
            "cms_npi_registry": "provider_or_facility",
            "dcyf_child_care_check": "childcare_provider",
            "hca_managed_care": "managed_care_plan",
        }
        return mapping.get(source_system, "recipient")

    @staticmethod
    def _publisher(source_system: str) -> str:
        return {
            "cms_npi_registry": "Centers for Medicare & Medicaid Services",
            "dcyf_child_care_check": "Washington State Department of Children, Youth, and Families",
            "hca_managed_care": "Washington State Health Care Authority",
        }.get(source_system, "Official public source")

    @staticmethod
    def _secondary_publisher(source_system: str) -> str:
        return {
            "cms_npi_registry": "Washington State Department of Health",
            "dcyf_child_care_check": "Washington State Department of Children, Youth, and Families",
            "hca_managed_care": "Washington State Health Care Authority",
        }.get(source_system, "Official public source")

    @staticmethod
    def _source_title(source_system: str) -> str:
        return {
            "cms_npi_registry": "CMS NPI Registry API reference",
            "dcyf_child_care_check": "DCYF Child Care Check",
            "hca_managed_care": "Apple Health managed care organizations",
        }.get(source_system, "Official public identifier source")

    @staticmethod
    def _secondary_source_title(source_system: str) -> str:
        return {
            "cms_npi_registry": "Washington DOH provider credential search",
            "dcyf_child_care_check": "Find Child Care WA search",
            "hca_managed_care": "Apple Health managed care reports",
        }.get(source_system, "Secondary official source")

    @staticmethod
    def _normalize_city_summary(row: dict[str, str]) -> dict[str, object]:
        return {
            "city": row["city"],
            "state": row["state"],
            "site_count": int(row["site_count"]),
            "recipient_count": int(row["recipient_count"]),
            "total_amount": float(row["total_amount"]),
            "payment_count": int(row["payment_count"]),
            "focus_areas": row["focus_areas"],
            "top_agencies": row["top_agencies"],
        }

    @staticmethod
    def _normalize_county_summary(row: dict[str, str]) -> dict[str, object]:
        return {
            "county_name": row["county_name"],
            "county_fips": row["county_fips"],
            "state": row["state"],
            "site_count": int(row["site_count"]),
            "recipient_count": int(row["recipient_count"]),
            "total_amount": float(row["total_amount"]),
            "payment_count": int(row["payment_count"]),
            "spend_per_site": float(row["spend_per_site"]),
            "normalized_total_spend": float(row["normalized_total_spend"]),
            "recipient_names": row["recipient_names"],
            "source_systems": row["source_systems"],
            "focus_areas": row["focus_areas"],
            "sectors": row["sectors"],
            "top_agencies": row["top_agencies"],
        }

    @staticmethod
    def _normalize_cluster_summary(row: dict[str, str]) -> dict[str, object]:
        return {
            "cluster_id": row["cluster_id"],
            "cluster_type": row["cluster_type"],
            "cluster_size": int(row["cluster_size"]),
            "city": row["city"],
            "state": row["state"],
            "zip_code": row["zip_code"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "total_amount": float(row["total_amount"]),
            "payment_count": int(row["payment_count"]),
            "recipient_names": row["recipient_names"],
            "focus_areas": row["focus_areas"],
            "top_agencies": row["top_agencies"],
        }

    @staticmethod
    def _normalize_review(row: dict[str, str]) -> dict[str, object]:
        return {
            "review_id": row["review_id"],
            "review_status": row["review_status"],
            "indicator_label": row["indicator_label"],
            "cluster_id": row["cluster_id"],
            "cluster_type": row["cluster_type"],
            "cluster_size": int(row["cluster_size"]),
            "city": row["city"],
            "state": row["state"],
            "zip_code": row["zip_code"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "recipient_names": row["recipient_names"],
            "focus_areas": row["focus_areas"],
            "top_agencies": row["top_agencies"],
            "total_amount": float(row["total_amount"]),
            "payment_count": int(row["payment_count"]),
            "review_priority": row["review_priority"],
            "rationale": row["rationale"],
            "methodology": row["methodology"],
            "source_traceability": row["source_traceability"],
        }
