from __future__ import annotations

import json
from pathlib import Path

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"

SOS_SOURCES = [
    {
        "source_key": "wa_sos_corporation_search_page",
        "publisher": "Washington Secretary of State",
        "title": "Corporation Search",
        "source_url": "https://ccfs.sos.wa.gov/ng-app/view/businesssearch/searchBusiness.html",
        "access_url": "https://ccfs.sos.wa.gov/#/BusinessSearch",
        "source_type": "official_search_portal",
        "update_frequency": "search-tool-based",
        "traceability_notes": (
            "The public search page states business information filed with the Office of the "
            "Secretary of State is available for public view and can be searched by business name or UBI."
        ),
    },
    {
        "source_key": "wa_sos_api_configuration",
        "publisher": "Washington Secretary of State",
        "title": "CCFS API Configuration",
        "source_url": "https://ccfs.sos.wa.gov/apiURL.js",
        "access_url": "https://ccfs.sos.wa.gov/apiURL.js",
        "source_type": "official_application_configuration",
        "update_frequency": "application-based",
        "traceability_notes": (
            "The official application configuration exposes the public API base URL used by the "
            "Corporation Search frontend."
        ),
    },
    {
        "source_key": "wa_sos_business_search_endpoint",
        "publisher": "Washington Secretary of State",
        "title": "Business Search API Endpoint",
        "source_url": "https://ccfs.sos.wa.gov/bundles/ccfs-js?version=20260226.1",
        "access_url": "https://ccfs-api.prod.sos.wa.gov/api/BusinessSearch/GetBusinessSearchDetails",
        "source_type": "official_application_endpoint",
        "update_frequency": "application-based",
        "traceability_notes": (
            "The official JavaScript bundle maps the public Corporation Search UI to the "
            "BusinessSearch/GetBusinessSearchDetails endpoint and sets the X-reCAPTCHA header "
            "before requests are sent."
        ),
    },
    {
        "source_key": "wa_sos_business_information_endpoint",
        "publisher": "Washington Secretary of State",
        "title": "Business Information API Endpoint",
        "source_url": "https://ccfs.sos.wa.gov/bundles/ccfs-js?version=20260226.1",
        "access_url": "https://ccfs-api.prod.sos.wa.gov/api/BusinessSearch/BusinessInformation",
        "source_type": "official_application_endpoint",
        "update_frequency": "application-based",
        "traceability_notes": (
            "The official JavaScript bundle maps the public Business Information page to the "
            "BusinessSearch/BusinessInformation endpoint using a businessID query parameter."
        ),
    },
    {
        "source_key": "wa_sos_business_information_template",
        "publisher": "Washington Secretary of State",
        "title": "Business Information Template",
        "source_url": "https://ccfs.sos.wa.gov/ng-app/view/businesssearch/businessInformation.html",
        "access_url": "https://ccfs.sos.wa.gov/ng-app/view/businesssearch/businessInformation.html",
        "source_type": "official_template",
        "update_frequency": "application-based",
        "traceability_notes": (
            "The public template shows the fields displayed for business records, including "
            "business name, UBI number, status, type, principal office addresses, jurisdiction, "
            "formation date, inactive date, and nature of business."
        ),
    },
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def export_sos_source_registry() -> None:
    output_path = _normalized_dir() / "sos_source_registry.json"
    output_path.write_text(json.dumps(SOS_SOURCES, indent=2), encoding="utf-8")
    print(f"SOS source registry: {output_path}")
