from __future__ import annotations

import csv
import json
from pathlib import Path

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _read_csv(name: str) -> list[dict[str, str]]:
    path = _normalized_dir() / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _hca_identifier_links(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for row in rows:
        links.append(
            {
                "canonical_recipient_id": row["canonical_recipient_id"],
                "state_code": row["state_code"],
                "source_slug": row["source_slug"],
                "sector": "healthcare",
                "source_system": "hca_managed_care",
                "identifier_type": "apple_health_plan_code",
                "identifier_value": row["plan_code"],
                "identifier_display": row["official_plan_name"],
                "link_status": "verified",
                "linkage_method": row["match_type"],
                "linkage_explanation": row["match_explanation"],
                "source_record_name": row["official_plan_name"],
                "source_record_status": "official_plan",
                "source_record_location": "",
                "source_url_primary": row["source_url_primary"],
                "source_url_secondary": row["source_url_secondary"],
                "total_amount": row["total_amount"],
                "payment_count": row["payment_count"],
                "top_agency": row["top_agency"],
                "primary_focus_area": row["primary_focus_area"],
                "focus_areas": row["focus_areas"],
            }
        )
    return links


def _dcyf_identifier_links(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for row in rows:
        common = {
            "canonical_recipient_id": row["canonical_recipient_id"],
            "state_code": row["state_code"],
            "source_slug": row["source_slug"],
            "sector": "childcare",
            "source_system": "dcyf_child_care_check",
            "link_status": "verified",
            "linkage_method": row["verification_route"],
            "linkage_explanation": row["match_explanation"],
            "source_record_name": row["provider_display_name"],
            "source_record_status": row["license_status"],
            "source_record_location": row["provider_location"],
            "source_url_primary": row["source_url_primary"],
            "source_url_secondary": row["source_url_secondary"],
            "total_amount": row["total_amount"],
            "payment_count": row["payment_count"],
            "top_agency": row["top_agency"],
            "primary_focus_area": "childcare_and_early_learning",
            "focus_areas": "childcare_and_early_learning",
        }
        links.append(
            common
            | {
                "identifier_type": "dcyf_provider_record_id",
                "identifier_value": row["provider_record_id"],
                "identifier_display": row["provider_business_name"] or row["provider_display_name"],
            }
        )
        if row["license_record_id"]:
            links.append(
                common
                | {
                    "identifier_type": "dcyf_license_record_id",
                    "identifier_value": row["license_record_id"],
                    "identifier_display": row["facility_type"],
                }
            )
    return links


def _doh_candidate_links(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for row in rows:
        links.append(
            {
                "canonical_recipient_id": row["canonical_recipient_id"],
                "state_code": row["state_code"],
                "source_slug": row["source_slug"],
                "sector": "healthcare_or_hospice",
                "source_system": "doh_provider_or_facility_search",
                "identifier_type": "search_candidate",
                "identifier_value": row["search_name"],
                "identifier_display": row["search_name"],
                "link_status": row["verification_status"],
                "linkage_method": row["verification_route"],
                "linkage_explanation": row["verification_rationale"],
                "source_record_name": "",
                "source_record_status": "",
                "source_record_location": "",
                "source_url_primary": row["source_url_primary"],
                "source_url_secondary": row["source_url_secondary"],
                "total_amount": row["total_amount"],
                "payment_count": row["payment_count"],
                "top_agency": row["top_agency"],
                "primary_focus_area": row["primary_focus_area"],
                "focus_areas": row["focus_areas"],
            }
        )
    return links


def build_provider_identity_bridge() -> None:
    hca_rows = _read_csv("hca_managed_care_matches.csv")
    dcyf_rows = _read_csv("dcyf_childcare_verified_matches.csv")
    doh_rows = _read_csv("doh_verification_candidates.csv")
    npi_rows = _read_csv("npi_facility_verified_matches.csv")

    verified_links = [*_hca_identifier_links(hca_rows), *_dcyf_identifier_links(dcyf_rows)]
    for row in npi_rows:
        verified_links.append(
            {
                "canonical_recipient_id": row["canonical_recipient_id"],
                "state_code": row["state_code"],
                "source_slug": row["source_slug"],
                "sector": "healthcare_or_hospice",
                "source_system": "cms_npi_registry",
                "identifier_type": "npi",
                "identifier_value": row["npi_number"],
                "identifier_display": row["organization_name"],
                "link_status": "verified",
                "linkage_method": row["verification_route"],
                "linkage_explanation": row["match_explanation"],
                "source_record_name": row["organization_name"],
                "source_record_status": row["organization_status"],
                "source_record_location": row["location_address"],
                "source_url_primary": row["source_url_primary"],
                "source_url_secondary": row["source_url_secondary"],
                "total_amount": row["total_amount"],
                "payment_count": row["payment_count"],
                "top_agency": row["top_agency"],
                "primary_focus_area": row["primary_focus_area"],
                "focus_areas": row["focus_areas"],
            }
        )
    candidate_links = _doh_candidate_links(doh_rows)

    verified_path = _normalized_dir() / "recipient_identifier_links.csv"
    candidate_path = _normalized_dir() / "recipient_identifier_candidates.csv"
    summary_path = _normalized_dir() / "recipient_identifier_summary.json"

    fieldnames = [
        "canonical_recipient_id",
        "state_code",
        "source_slug",
        "sector",
        "source_system",
        "identifier_type",
        "identifier_value",
        "identifier_display",
        "link_status",
        "linkage_method",
        "linkage_explanation",
        "source_record_name",
        "source_record_status",
        "source_record_location",
        "source_url_primary",
        "source_url_secondary",
        "total_amount",
        "payment_count",
        "top_agency",
        "primary_focus_area",
        "focus_areas",
    ]

    with verified_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(verified_links, key=lambda item: float(item["total_amount"]), reverse=True):
            writer.writerow(row)

    with candidate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(candidate_links, key=lambda item: float(item["total_amount"]), reverse=True):
            writer.writerow(row)

    summary = {
        "state_code": STATE_CODE,
        "source_slug": SOURCE_SLUG,
        "verified_identifier_count": len(verified_links),
        "verified_recipient_count": len({row["canonical_recipient_id"] for row in verified_links}),
        "candidate_identifier_count": len(candidate_links),
        "candidate_recipient_count": len({row["canonical_recipient_id"] for row in candidate_links}),
        "verified_by_system": {
            "hca_managed_care": len(hca_rows),
            "dcyf_child_care_check": len(dcyf_rows),
            "cms_npi_registry": len(npi_rows),
        },
        "candidate_by_system": {
            "doh_provider_or_facility_search": len(doh_rows),
        },
        "methodology_notes": [
            "Verified links require a source-backed identifier or official program code from an official Washington source.",
            "Healthcare and hospice DOH rows remain candidate-only until an official facility or credential identifier is confirmed.",
            "This bridge is designed to let the platform prefer provider, plan, and license identifiers over business-name-only linkage.",
        ],
        "next_priority_sources": [
            "DOH facility and credential identifiers for healthcare and hospice recipients",
            "Additional HCA provider-level identifiers beyond managed care plan organizations",
            "Commerce and housing-program recipient registries for homelessness and shelter-related entities",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Verified identifier links: {len(verified_links)}")
    print(f"Candidate identifier links: {len(candidate_links)}")
    print(f"Verified identifier CSV: {verified_path}")
    print(f"Candidate identifier CSV: {candidate_path}")
    print(f"Identifier summary JSON: {summary_path}")
