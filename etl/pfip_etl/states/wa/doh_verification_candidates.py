from __future__ import annotations

import csv
from pathlib import Path

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"

PROVIDER_SEARCH_PAGE = "https://doh.wa.gov/licenses-permits-and-certificates/provider-credential-search"
PROVIDER_SEARCH_TOOL = "https://fortress.wa.gov/doh/providercredentialsearch/"
PROVIDER_DATASET_META = "https://data.wa.gov/api/views/qxh8-f4bd"
HOSPICE_PAGE = "https://doh.wa.gov/licenses-permits-and-certificates/facilities-z/hospice-agencies"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _canonical_recipient_path() -> Path:
    return _normalized_dir() / "canonical_recipients.csv"


def _needs_doh_verification(row: dict[str, str]) -> tuple[bool, str, str]:
    name = row["canonical_recipient_name"].upper()
    primary_focus_area = row["primary_focus_area"]

    if "HOSPICE" in name:
        return (
            True,
            "hospice_agency_license_verification",
            "Recipient name contains hospice terminology; DOH hospice facility licensing is a relevant official verification route.",
        )

    if any(term in name for term in ("HOSPITAL", "CLINIC", "PHARMACY", "MEDICAL", "DENTAL", "LASER", "COUNSEL")):
        return (
            True,
            "provider_or_facility_search",
            "Recipient name contains healthcare-service terminology that should be checked against DOH provider or facility licensing sources.",
        )

    if primary_focus_area == "healthcare_and_hospice":
        return (
            True,
            "provider_or_facility_search",
            "Recipient is in the healthcare-focused payment bucket and should be reviewed against DOH credential or facility sources.",
        )

    return (False, "", "")


def build_doh_verification_candidates() -> None:
    input_path = _canonical_recipient_path()
    if not input_path.exists():
        raise SystemExit(
            f"Missing canonical recipients at {input_path}. Run the WA recipient resolution pipeline first."
        )

    with input_path.open(encoding="utf-8") as handle:
        recipients = list(csv.DictReader(handle))

    candidates: list[dict[str, str]] = []
    for recipient in recipients:
        include, verification_route, rationale = _needs_doh_verification(recipient)
        if not include:
            continue

        primary_source = HOSPICE_PAGE if verification_route == "hospice_agency_license_verification" else PROVIDER_SEARCH_PAGE
        secondary_source = PROVIDER_SEARCH_TOOL

        candidates.append(
            {
                "canonical_recipient_id": recipient["canonical_recipient_id"],
                "state_code": STATE_CODE,
                "source_slug": SOURCE_SLUG,
                "canonical_recipient_name": recipient["canonical_recipient_name"],
                "canonical_name_standardized": recipient["canonical_name_standardized"],
                "primary_focus_area": recipient["primary_focus_area"],
                "verification_status": "candidate_only",
                "verification_route": verification_route,
                "verification_rationale": rationale,
                "search_name": recipient["canonical_recipient_name"],
                "source_url_primary": primary_source,
                "source_url_secondary": secondary_source,
                "source_url_dataset": PROVIDER_DATASET_META,
                "total_amount": recipient["total_amount"],
                "payment_count": recipient["payment_count"],
                "focus_areas": recipient["focus_areas"],
                "top_agency": recipient["top_agency"],
            }
        )

    output_path = _normalized_dir() / "doh_verification_candidates.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "canonical_recipient_id",
            "state_code",
            "source_slug",
            "canonical_recipient_name",
            "canonical_name_standardized",
            "primary_focus_area",
            "verification_status",
            "verification_route",
            "verification_rationale",
            "search_name",
            "source_url_primary",
            "source_url_secondary",
            "source_url_dataset",
            "total_amount",
            "payment_count",
            "focus_areas",
            "top_agency",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in sorted(candidates, key=lambda item: float(item["total_amount"]), reverse=True):
            writer.writerow(candidate)

    print(f"Canonical recipients scanned: {len(recipients)}")
    print(f"DOH verification candidates: {len(candidates)}")
    print(f"Candidate CSV: {output_path}")
