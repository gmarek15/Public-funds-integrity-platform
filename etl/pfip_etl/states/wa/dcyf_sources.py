from __future__ import annotations

import json
from pathlib import Path

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"

DCYF_SOURCES = [
    {
        "source_key": "dcyf_find_child_care",
        "publisher": "Washington State Department of Children, Youth, and Families",
        "title": "Find Child Care / Early Learning",
        "source_url": "https://www.dcyf.wa.gov/services/earlylearning-childcare/find-child-care",
        "access_url": "https://www.dcyf.wa.gov/services/earlylearning-childcare/find-child-care",
        "source_type": "program_page",
        "update_frequency": "page-based",
        "traceability_notes": (
            "DCYF identifies Child Care Check as the search tool for licensed child care "
            "providers and early learning programs in Washington."
        ),
    },
    {
        "source_key": "dcyf_child_care_check",
        "publisher": "Washington State Department of Children, Youth, and Families",
        "title": "Child Care Check",
        "source_url": "https://www.dcyf.wa.gov/services/earlylearning-childcare/child-care-check",
        "access_url": "https://www.findchildcarewa.org/",
        "source_type": "official_search_tool",
        "update_frequency": "search-tool-based",
        "traceability_notes": (
            "DCYF states Child Care Check provides provider licensing status, complaint "
            "history, inspections, background-check status, and provider contact details."
        ),
    },
    {
        "source_key": "dcyf_child_care_complaints",
        "publisher": "Washington State Department of Children, Youth, and Families",
        "title": "Early Learning / Child Care Complaints",
        "source_url": "https://www.dcyf.wa.gov/safety/child-care-complaints",
        "access_url": "https://www.dcyf.wa.gov/safety/child-care-complaints",
        "source_type": "complaints_page",
        "update_frequency": "page-based",
        "traceability_notes": (
            "DCYF states valid complaint findings are posted on Child Care Check and that "
            "Child Care Check can be used to review provider licensing and complaint history."
        ),
    },
    {
        "source_key": "dcyf_wccc",
        "publisher": "Washington State Department of Children, Youth, and Families",
        "title": "Working Connections Child Care",
        "source_url": "https://www.dcyf.wa.gov/services/earlylearning-childcare/getting-help/wccc",
        "access_url": "https://www.dcyf.wa.gov/services/earlylearning-childcare/getting-help/wccc",
        "source_type": "program_page",
        "update_frequency": "page-based",
        "traceability_notes": (
            "DCYF states WCCC is a subsidy program where the state pays a portion of child care costs "
            "to participating providers after families qualify."
        ),
    },
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def export_dcyf_source_registry() -> None:
    output_path = _normalized_dir() / "dcyf_source_registry.json"
    output_path.write_text(json.dumps(DCYF_SOURCES, indent=2), encoding="utf-8")
    print(f"DCYF source registry: {output_path}")
