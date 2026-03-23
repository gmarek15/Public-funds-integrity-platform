from __future__ import annotations

import json
from pathlib import Path

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"

DOH_SOURCES = [
    {
        "source_key": "doh_provider_credential_dataset",
        "publisher": "Washington State Department of Health",
        "title": "Health Care Provider Credential Data",
        "source_url": "https://data.wa.gov/api/views/qxh8-f4bd",
        "access_url": "https://data.wa.gov/resource/qxh8-f4bd.csv",
        "source_type": "open_data_dataset",
        "update_frequency": "daily",
        "traceability_notes": (
            "DOH states this dataset is a primary source for verification of credentials, "
            "updated daily at 10:00 a.m. and extracted from the primary database at 2:00 a.m."
        ),
    },
    {
        "source_key": "doh_provider_or_facility_search",
        "publisher": "Washington State Department of Health",
        "title": "Provider Credential or Facility Search",
        "source_url": "https://doh.wa.gov/licenses-permits-and-certificates/provider-credential-search",
        "access_url": "https://fortress.wa.gov/doh/providercredentialsearch/",
        "source_type": "official_search_portal",
        "update_frequency": "daily",
        "traceability_notes": (
            "DOH states this is a primary source for verification of credentials and supports "
            "search by credential number, individual name, or business name."
        ),
    },
    {
        "source_key": "doh_hospice_agencies_page",
        "publisher": "Washington State Department of Health",
        "title": "Hospice Agencies",
        "source_url": "https://doh.wa.gov/licenses-permits-and-certificates/facilities-z/hospice-agencies",
        "access_url": "https://doh.wa.gov/licenses-permits-and-certificates/facilities-z/hospice-agencies",
        "source_type": "facility_program_page",
        "update_frequency": "page-based",
        "traceability_notes": (
            "DOH hospice facility page links directly to license verification and facility-specific "
            "licensing information for hospice agencies."
        ),
    },
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def export_doh_source_registry() -> None:
    output_path = _normalized_dir() / "doh_source_registry.json"
    output_path.write_text(json.dumps(DOH_SOURCES, indent=2), encoding="utf-8")
    print(f"DOH source registry: {output_path}")
