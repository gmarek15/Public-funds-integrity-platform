from __future__ import annotations

import csv
from pathlib import Path

from pfip_etl.io import ensure_directory
from pfip_etl.states.wa.common import standardize_alias_tokens

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"
ENRICHMENT_SLUG = "hca_managed_care"

HCA_MANAGED_CARE_URL = (
    "https://www.hca.wa.gov/free-or-low-cost-health-care/"
    "i-need-medical-dental-or-vision-care/apple-health-managed-care"
)
HCA_REPORTS_URL = (
    "https://www.hca.wa.gov/about-hca/programs-and-initiatives/"
    "apple-health-medicaid/apple-health-medicaid-and-managed-care-reports"
)

HCA_MANAGED_CARE_PLANS = [
    {
        "official_plan_name": "Community Health Plan of Washington",
        "plan_code": "CHPW",
        "aliases": [
            "COMMUNITY HEALTH PLAN OF WASHINGTON",
            "COMMUNITY HEALTH PLAN OF WASHING",
            "COMMUNITY HEALTH PLAN OF WASH",
            "CHPW",
        ],
    },
    {
        "official_plan_name": "Coordinated Care",
        "plan_code": "CC",
        "aliases": [
            "COORDINATED CARE",
            "COORDINATED CARE OF WASHINGTON",
            "COORDINATED CARE OF WASHINGTON INC",
            "APPLE HEALTH CORE CONNECTIONS",
            "CCW",
        ],
    },
    {
        "official_plan_name": "Molina Healthcare of Washington, Inc.",
        "plan_code": "MHW",
        "aliases": [
            "MOLINA HEALTHCARE OF WASHINGTON",
            "MOLINA HEALTHCARE OF WA",
            "MOLINA HEALTHCARE OF WA INC",
            "MHW",
        ],
    },
    {
        "official_plan_name": "UnitedHealthcare Community Plan",
        "plan_code": "UHC",
        "aliases": [
            "UNITEDHEALTHCARE COMMUNITY PLAN",
            "UNITED HEALTH CARE OF WASHINGTON",
            "UNITED HEALTHCARE OF WASHINGTON",
            "UHC",
        ],
    },
    {
        "official_plan_name": "Wellpoint Washington",
        "plan_code": "WLP",
        "aliases": [
            "WELLPOINT WASHINGTON",
            "WELLPOINT WASHINGTON INC",
            "WLP",
        ],
    },
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _canonical_recipient_path() -> Path:
    return _normalized_dir() / "canonical_recipients.csv"


def _build_alias_index() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for plan in HCA_MANAGED_CARE_PLANS:
        for alias in plan["aliases"]:
            index[standardize_alias_tokens(alias)] = {
                "official_plan_name": plan["official_plan_name"],
                "plan_code": plan["plan_code"],
            }
    return index


def build_hca_managed_care_enrichment() -> None:
    input_path = _canonical_recipient_path()
    if not input_path.exists():
        raise SystemExit(
            f"Missing canonical recipients at {input_path}. Run the WA recipient resolution pipeline first."
        )

    alias_index = _build_alias_index()
    with input_path.open(encoding="utf-8") as handle:
        recipients = list(csv.DictReader(handle))

    matches: list[dict[str, str]] = []
    for recipient in recipients:
        standardized_name = standardize_alias_tokens(recipient["canonical_name_standardized"])
        if standardized_name not in alias_index:
            continue

        plan = alias_index[standardized_name]
        matches.append(
            {
                "canonical_recipient_id": recipient["canonical_recipient_id"],
                "state_code": STATE_CODE,
                "source_slug": SOURCE_SLUG,
                "enrichment_slug": ENRICHMENT_SLUG,
                "canonical_recipient_name": recipient["canonical_recipient_name"],
                "canonical_name_standardized": recipient["canonical_name_standardized"],
                "primary_focus_area": recipient["primary_focus_area"],
                "official_plan_name": plan["official_plan_name"],
                "plan_code": plan["plan_code"],
                "match_type": "official_hca_managed_care_alias",
                "match_explanation": (
                    "Matched canonical recipient to an official Apple Health managed care organization "
                    "name or acronym published by HCA."
                ),
                "source_url_primary": HCA_MANAGED_CARE_URL,
                "source_url_secondary": HCA_REPORTS_URL,
                "total_amount": recipient["total_amount"],
                "payment_count": recipient["payment_count"],
                "top_agency": recipient["top_agency"],
                "focus_areas": recipient["focus_areas"],
            }
        )

    output_path = _normalized_dir() / "hca_managed_care_matches.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "canonical_recipient_id",
            "state_code",
            "source_slug",
            "enrichment_slug",
            "canonical_recipient_name",
            "canonical_name_standardized",
            "primary_focus_area",
            "official_plan_name",
            "plan_code",
            "match_type",
            "match_explanation",
            "source_url_primary",
            "source_url_secondary",
            "total_amount",
            "payment_count",
            "top_agency",
            "focus_areas",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for match in sorted(matches, key=lambda item: float(item["total_amount"]), reverse=True):
            writer.writerow(match)

    print(f"Canonical recipients scanned: {len(recipients)}")
    print(f"HCA managed care matches: {len(matches)}")
    print(f"Match CSV: {output_path}")
