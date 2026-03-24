from __future__ import annotations

import csv
from pathlib import Path

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"

MANUAL_REVIEW_MARKERS = {
    "CITY OF",
    "COUNTY OF",
    "PORT OF",
    "STATE OF WASHINGTON",
    "WASHINGTON STATE",
    "SCHOOL DISTRICT",
    "PUBLIC UTILITY DISTRICT",
    "PUD NO",
    "FIRE DISTRICT",
    "HOUSING AUTHORITY",
    "TRIBE",
    "TRIBAL",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _canonical_recipient_path() -> Path:
    return _normalized_dir() / "canonical_recipients.csv"


def _candidate_route(name: str) -> tuple[str, str]:
    upper_name = name.upper()
    for marker in MANUAL_REVIEW_MARKERS:
        if marker in upper_name:
            return (
                "manual_non_sos_entity_review",
                "Recipient name suggests a government, tribal, or other special entity that may not resolve through SOS business records.",
            )

    return (
        "sos_business_entity_review",
        "Recipient name appears suitable for Washington Secretary of State business-entity verification via business name and UBI.",
    )


def build_sos_ubi_candidates() -> None:
    input_path = _canonical_recipient_path()
    if not input_path.exists():
        raise SystemExit(
            f"Missing canonical recipients at {input_path}. Run the WA recipient resolution pipeline first."
        )

    with input_path.open(encoding="utf-8") as handle:
        recipients = sorted(
            csv.DictReader(handle),
            key=lambda item: float(item["total_amount"]),
            reverse=True,
        )

    rows: list[dict[str, str]] = []
    for recipient in recipients:
        route, explanation = _candidate_route(recipient["canonical_recipient_name"])
        rows.append(
            {
                "canonical_recipient_id": recipient["canonical_recipient_id"],
                "state_code": STATE_CODE,
                "source_slug": SOURCE_SLUG,
                "canonical_recipient_name": recipient["canonical_recipient_name"],
                "canonical_name_standardized": recipient["canonical_name_standardized"],
                "primary_focus_area": recipient["primary_focus_area"],
                "focus_areas": recipient["focus_areas"],
                "candidate_route": route,
                "candidate_explanation": explanation,
                "search_name": recipient["canonical_recipient_name"],
                "alias_examples": recipient["alias_examples"],
                "total_amount": recipient["total_amount"],
                "payment_count": recipient["payment_count"],
                "top_agency": recipient["top_agency"],
            }
        )

    output_path = _normalized_dir() / "sos_ubi_candidates.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "canonical_recipient_id",
            "state_code",
            "source_slug",
            "canonical_recipient_name",
            "canonical_name_standardized",
            "primary_focus_area",
            "focus_areas",
            "candidate_route",
            "candidate_explanation",
            "search_name",
            "alias_examples",
            "total_amount",
            "payment_count",
            "top_agency",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    routed_to_sos = sum(1 for row in rows if row["candidate_route"] == "sos_business_entity_review")
    print(f"SOS candidate rows: {len(rows)}")
    print(f"SOS-search candidates: {routed_to_sos}")
    print(f"Candidate CSV: {output_path}")
