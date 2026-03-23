from __future__ import annotations

import csv
from pathlib import Path

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"

FIND_CHILD_CARE_URL = "https://www.dcyf.wa.gov/services/earlylearning-childcare/find-child-care"
CHILD_CARE_CHECK_PAGE = "https://www.dcyf.wa.gov/services/earlylearning-childcare/child-care-check"
CHILD_CARE_CHECK_TOOL = "https://www.findchildcarewa.org/"
CHILD_CARE_COMPLAINTS_URL = "https://www.dcyf.wa.gov/safety/child-care-complaints"
WCCC_URL = "https://www.dcyf.wa.gov/services/earlylearning-childcare/getting-help/wccc"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _canonical_recipient_path() -> Path:
    return _normalized_dir() / "canonical_recipients.csv"


def _childcare_route(row: dict[str, str]) -> tuple[bool, str, str]:
    name = row["canonical_recipient_name"].upper()
    primary_focus_area = row["primary_focus_area"]
    top_agency = row["top_agency"].upper()

    childcare_terms = (
        "CHILD",
        "DAYCARE",
        "DAY CARE",
        "EARLY LEARNING",
        "PRESCHOOL",
        "HEAD START",
        "ECEAP",
        "MONTESSORI",
        "LEARNING CENTER",
    )
    institutional_terms = (
        "UNIVERSITY",
        "HOSPITAL",
        "HEALTHCARE",
        "STAFFING",
        "SCHOOL DISTRICT",
        "SCHOOLS",
        "ESD",
        "EDUC SVC DIST",
        "DSHS",
        "DOH",
        "CORRECTIONAL",
        "COUNTY",
        "CITY OF",
        "HEALTH DIST",
        "PUBLIC",
    )

    has_childcare_term = any(term in name for term in childcare_terms)
    is_institutional = any(term in name for term in institutional_terms)

    if has_childcare_term and not is_institutional:
        return (
            True,
            "child_care_check_licensing_review",
            "Recipient name contains child care or early learning terminology that should be checked in DCYF Child Care Check.",
        )

    if primary_focus_area == "childcare_and_early_learning" and not is_institutional:
        return (
            True,
            "child_care_check_licensing_review",
            "Recipient appears in the child care / early learning payment flow and should be reviewed in Child Care Check for licensing, complaint history, and inspections.",
        )

    if primary_focus_area == "childcare_and_early_learning" or "CHILDREN, YOUTH, AND FAMILIES" in top_agency:
        return (
            True,
            "childcare_program_counterparty_review",
            "Recipient appears in child care funding flows but may be a school, hospital, government, or other counterparty rather than a licensed child care provider.",
        )

    return (False, "", "")


def build_dcyf_childcare_candidates() -> None:
    input_path = _canonical_recipient_path()
    if not input_path.exists():
        raise SystemExit(
            f"Missing canonical recipients at {input_path}. Run the WA recipient resolution pipeline first."
        )

    with input_path.open(encoding="utf-8") as handle:
        recipients = list(csv.DictReader(handle))

    candidates: list[dict[str, str]] = []
    for recipient in recipients:
        include, verification_route, rationale = _childcare_route(recipient)
        if not include:
            continue

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
                "source_url_primary": CHILD_CARE_CHECK_PAGE,
                "source_url_secondary": CHILD_CARE_CHECK_TOOL,
                "source_url_complaints": CHILD_CARE_COMPLAINTS_URL,
                "source_url_program": WCCC_URL,
                "source_url_directory": FIND_CHILD_CARE_URL,
                "total_amount": recipient["total_amount"],
                "payment_count": recipient["payment_count"],
                "focus_areas": recipient["focus_areas"],
                "top_agency": recipient["top_agency"],
            }
        )

    output_path = _normalized_dir() / "dcyf_childcare_candidates.csv"
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
            "source_url_complaints",
            "source_url_program",
            "source_url_directory",
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
    print(f"DCYF childcare candidates: {len(candidates)}")
    print(f"Candidate CSV: {output_path}")
