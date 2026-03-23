from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from pfip_etl.io import ensure_directory
from pfip_etl.states.wa.common import normalize_vendor_name

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"

FOCUS_AREAS = {
    "healthcare_and_hospice": "Healthcare providers, clinics, pharmacies, hospice, counseling, and hospital-linked payments.",
    "childcare_and_early_learning": "Child care centers, early learning providers, and youth/family service operators.",
    "housing_and_homelessness": "Housing, shelter, faith-based assistance, and homelessness-related recipient patterns.",
    "long_term_care_and_residential_support": "Adult family homes, residential support, and long-term care style recipients.",
    "public_assistance_and_client_support": "Direct provider or client-support payments that do not yet map cleanly to a narrower program area.",
    "government_and_utility_entities": "Government districts, utilities, and public-sector counterparties.",
    "operations_and_procurement": "General vendors, contractors, and operational suppliers.",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _raw_csv_path() -> Path:
    return _data_root() / "raw" / "wa" / SOURCE_SLUG / "VendorPayments2527.payments.csv"


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def classify_focus_area(row: dict[str, str]) -> tuple[str, list[str]]:
    agency = row["agency_name"].upper()
    category = row["category_name"].upper()
    subcategory = row["subcategory_name"].upper()
    vendor = row["vendor_name_raw"].upper()
    reasons: list[str] = []

    childcare_terms = ("CHILD", "EARLY LEARNING", "DAYCARE", "DAY CARE", "PRESCHOOL")
    healthcare_terms = (
        "HOSPICE",
        "HOSPITAL",
        "CLINIC",
        "HEALTH",
        "PHARMACY",
        "COUNSEL",
        "MEDICAL",
        "DENTAL",
        "LASER",
        "THERAP",
        "BEHAVIORAL",
    )
    housing_terms = ("HOUSING", "HOMELESS", "SHELTER", "METHODIST", "MISSION", "VILLAGE", "APARTMENTS")
    residential_terms = ("AFH", "ADULT FAMILY", "HOME CARE", "SUPPORTED LIVING", "RESIDENTIAL")
    government_terms = ("COUNTY", "CITY OF", "DISTRICT", "UTILITY", "PUBLIC HOSPITAL", "STATE OF")

    if "CHILDREN, YOUTH, AND FAMILIES" in agency or any(term in vendor for term in childcare_terms):
        reasons.append("Matched child care or youth/family rule from agency or vendor name.")
        return "childcare_and_early_learning", reasons

    if "HEALTH CARE AUTHORITY" in agency or "HEALTH" == agency or any(term in vendor for term in healthcare_terms):
        reasons.append("Matched healthcare or hospice rule from agency or vendor name.")
        return "healthcare_and_hospice", reasons

    if "SOCIAL AND HEALTH SERVICES" in agency and any(term in vendor for term in residential_terms):
        reasons.append("Matched long-term care or residential-support rule from agency and vendor pattern.")
        return "long_term_care_and_residential_support", reasons

    if "COMMERCE" in agency and ("GRANTS" in category or "OTHER GRANTS" in subcategory):
        if any(term in vendor for term in housing_terms):
            reasons.append("Matched housing or homelessness rule from Commerce grant payment and vendor pattern.")
            return "housing_and_homelessness", reasons
        reasons.append("Matched Commerce grants rule; retained as housing/homelessness-oriented default bucket.")
        return "housing_and_homelessness", reasons

    if any(term in vendor for term in government_terms):
        reasons.append("Matched public-sector or utility counterparty rule from vendor name.")
        return "government_and_utility_entities", reasons

    if "DIRECT PAYMENTS TO PROVIDERS" in subcategory or "GRANTS, BENEFITS & CLIENT SERVICES" in category:
        reasons.append("Matched provider/client-support rule from fiscal category structure.")
        return "public_assistance_and_client_support", reasons

    reasons.append("Fell back to general operations/procurement bucket.")
    return "operations_and_procurement", reasons


def _load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_open_checkbook_rollups() -> None:
    csv_path = _raw_csv_path()
    if not csv_path.exists():
        raise SystemExit(
            f"Missing raw CSV at {csv_path}. Run the WA open checkbook puller first."
        )

    rows = _load_rows(csv_path)

    recipient_rollups: dict[str, dict] = {}
    area_totals: dict[str, dict[str, object]] = {}
    agency_area_totals: dict[tuple[str, str], dict[str, object]] = {}

    for row in rows:
        normalized_vendor = normalize_vendor_name(row["vendor_name_raw"])
        focus_area, reasons = classify_focus_area(row)
        amount = float(row["amount"])

        recipient = recipient_rollups.setdefault(
            normalized_vendor,
            {
                "state_code": STATE_CODE,
                "source_slug": SOURCE_SLUG,
                "vendor_name_normalized": normalized_vendor,
                "vendor_name_example": row["vendor_name_raw"],
                "focus_area": focus_area,
                "focus_area_reason": reasons[0],
                "payment_count": 0,
                "total_amount": 0.0,
                "agencies": Counter(),
                "categories": Counter(),
                "subcategories": Counter(),
                "fiscal_months": Counter(),
            },
        )
        recipient["payment_count"] += 1
        recipient["total_amount"] += amount
        recipient["agencies"][row["agency_name"]] += 1
        recipient["categories"][row["category_name"]] += 1
        recipient["subcategories"][row["subcategory_name"]] += 1
        recipient["fiscal_months"][f"{row['fiscal_year']}-{int(row['fiscal_month']):02d}"] += 1

        area = area_totals.setdefault(
            focus_area,
            {
                "focus_area": focus_area,
                "description": FOCUS_AREAS[focus_area],
                "payment_count": 0,
                "total_amount": 0.0,
                "unique_recipients": set(),
                "top_agencies": Counter(),
                "top_subcategories": Counter(),
            },
        )
        area["payment_count"] += 1
        area["total_amount"] += amount
        area["unique_recipients"].add(normalized_vendor)
        area["top_agencies"][row["agency_name"]] += 1
        area["top_subcategories"][row["subcategory_name"]] += 1

        agency_key = (row["agency_name"], focus_area)
        agency_area = agency_area_totals.setdefault(
            agency_key,
            {
                "agency_name": row["agency_name"],
                "focus_area": focus_area,
                "payment_count": 0,
                "total_amount": 0.0,
                "unique_recipients": set(),
                "top_subcategories": Counter(),
            },
        )
        agency_area["payment_count"] += 1
        agency_area["total_amount"] += amount
        agency_area["unique_recipients"].add(normalized_vendor)
        agency_area["top_subcategories"][row["subcategory_name"]] += 1

    output_dir = _normalized_dir()

    recipient_path = output_dir / "recipient_rollups.csv"
    with recipient_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "state_code",
            "source_slug",
            "vendor_name_normalized",
            "vendor_name_example",
            "focus_area",
            "focus_area_reason",
            "payment_count",
            "total_amount",
            "top_agency",
            "top_category",
            "top_subcategory",
            "active_month_count",
            "top_fiscal_month",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for recipient in sorted(
            recipient_rollups.values(),
            key=lambda item: (item["total_amount"], item["payment_count"]),
            reverse=True,
        ):
            writer.writerow(
                {
                    "state_code": recipient["state_code"],
                    "source_slug": recipient["source_slug"],
                    "vendor_name_normalized": recipient["vendor_name_normalized"],
                    "vendor_name_example": recipient["vendor_name_example"],
                    "focus_area": recipient["focus_area"],
                    "focus_area_reason": recipient["focus_area_reason"],
                    "payment_count": recipient["payment_count"],
                    "total_amount": f"{recipient['total_amount']:.2f}",
                    "top_agency": recipient["agencies"].most_common(1)[0][0],
                    "top_category": recipient["categories"].most_common(1)[0][0],
                    "top_subcategory": recipient["subcategories"].most_common(1)[0][0],
                    "active_month_count": len(recipient["fiscal_months"]),
                    "top_fiscal_month": recipient["fiscal_months"].most_common(1)[0][0],
                }
            )

    focus_area_path = output_dir / "focus_area_summary.json"
    focus_area_payload = []
    for area in sorted(area_totals.values(), key=lambda item: item["total_amount"], reverse=True):
        focus_area_payload.append(
            {
                "focus_area": area["focus_area"],
                "description": area["description"],
                "payment_count": area["payment_count"],
                "total_amount": round(float(area["total_amount"]), 2),
                "unique_recipient_count": len(area["unique_recipients"]),
                "top_agencies": area["top_agencies"].most_common(10),
                "top_subcategories": area["top_subcategories"].most_common(10),
            }
        )
    focus_area_path.write_text(json.dumps(focus_area_payload, indent=2), encoding="utf-8")

    agency_area_path = output_dir / "agency_focus_area_rollups.csv"
    with agency_area_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "agency_name",
            "focus_area",
            "payment_count",
            "total_amount",
            "unique_recipient_count",
            "top_subcategory",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in sorted(
            agency_area_totals.values(),
            key=lambda row: (row["total_amount"], row["payment_count"]),
            reverse=True,
        ):
            writer.writerow(
                {
                    "agency_name": item["agency_name"],
                    "focus_area": item["focus_area"],
                    "payment_count": item["payment_count"],
                    "total_amount": f"{item['total_amount']:.2f}",
                    "unique_recipient_count": len(item["unique_recipients"]),
                    "top_subcategory": item["top_subcategories"].most_common(1)[0][0],
                }
            )

    print(f"Input rows: {len(rows)}")
    print(f"Recipient rollups: {len(recipient_rollups)}")
    print(f"Recipient CSV: {recipient_path}")
    print(f"Focus area summary: {focus_area_path}")
    print(f"Agency/focus-area rollups: {agency_area_path}")
