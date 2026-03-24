from __future__ import annotations

import csv
import json
import os
import ssl
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pfip_etl.io import ensure_directory
from pfip_etl.states.wa.common import standardize_alias_tokens

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"
DEFAULT_MAX_CANDIDATES_PER_RUN = 100
NPI_API_URL = "https://npiregistry.cms.hhs.gov/api/"
NPI_API_PAGE_URL = "https://npiregistry.cms.hhs.gov/api-page"

FACILITY_NAME_KEYWORDS = {
    "HOSPITAL",
    "MEDICAL CENTER",
    "MEDICAL CTR",
    "CLINIC",
    "HOSPICE",
    "HEALTH SYSTEM",
    "HEALTH CENTER",
    "CANCER CENTER",
    "REHABILITATION",
    "BEHAVIORAL HEALTH",
}

FACILITY_TAXONOMY_KEYWORDS = {
    "HOSPITAL",
    "CLINIC/CENTER",
    "HOSPICE",
    "HOME HEALTH",
    "SKILLED NURSING",
    "PSYCHIATRIC",
    "REHABILITATION",
    "AMBULATORY SURGICAL",
    "LONG TERM CARE",
    "RESIDENTIAL TREATMENT",
    "GENERAL ACUTE CARE",
}

FACILITY_TAXONOMY_PRIORITY = [
    ("GENERAL ACUTE CARE HOSPITAL", 10),
    ("PSYCHIATRIC HOSPITAL", 9),
    ("HOSPICE CARE", 9),
    ("HOSPITAL", 8),
    ("REHABILITATION", 7),
    ("CLINIC/CENTER", 6),
    ("AMBULATORY SURGICAL", 5),
    ("HOME HEALTH", 5),
    ("SKILLED NURSING", 5),
    ("LONG TERM CARE", 4),
    ("RESIDENTIAL TREATMENT", 4),
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _doh_candidate_path() -> Path:
    return _normalized_dir() / "doh_verification_candidates.csv"


def _alias_path() -> Path:
    return _normalized_dir() / "recipient_alias_links.csv"


def _ssl_context():
    return ssl._create_unverified_context()


def _load_aliases() -> dict[str, list[str]]:
    alias_index: dict[str, list[str]] = {}
    with _alias_path().open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            alias_index.setdefault(row["canonical_recipient_id"], []).append(row["source_vendor_name_example"])
    return alias_index


def _is_facility_like(name: str) -> bool:
    upper_name = name.upper()
    return any(keyword in upper_name for keyword in FACILITY_NAME_KEYWORDS)


def _search_terms(candidate: dict[str, str], alias_index: dict[str, list[str]]) -> list[str]:
    terms = [candidate["canonical_recipient_name"], candidate["search_name"], *alias_index.get(candidate["canonical_recipient_id"], [])]
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        cleaned = " ".join((term or "").split()).strip()
        if not cleaned:
            continue
        key = cleaned.upper()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
    return deduped


def _query_npi(organization_name: str) -> dict:
    params = urlencode(
        {
            "version": "2.1",
            "organization_name": organization_name,
            "state": "WA",
            "enumeration_type": "NPI-2",
            "limit": "10",
        }
    )
    request = Request(
        f"{NPI_API_URL}?{params}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urlopen(request, timeout=30, context=_ssl_context()) as response:  # nosec: official public source
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _primary_taxonomy(result: dict) -> tuple[str, str]:
    taxonomies = result.get("taxonomies", [])
    for taxonomy in taxonomies:
        if taxonomy.get("primary"):
            return taxonomy.get("code", "") or "", taxonomy.get("desc", "") or ""
    if taxonomies:
        return taxonomies[0].get("code", "") or "", taxonomies[0].get("desc", "") or ""
    return "", ""


def _location_address(result: dict) -> str:
    for address in result.get("addresses", []):
        if address.get("address_purpose") == "LOCATION":
            parts = [
                address.get("address_1", ""),
                address.get("city", ""),
                address.get("state", ""),
                address.get("postal_code", ""),
            ]
            return ", ".join(part for part in parts if part)
    return ""


def _location_signature(result: dict) -> tuple[str, str, str, str]:
    for address in result.get("addresses", []):
        if address.get("address_purpose") == "LOCATION":
            street = " ".join(
                part.strip().upper()
                for part in [address.get("address_1", ""), address.get("address_2", "")]
                if part and part.strip()
            )
            postal_code = (address.get("postal_code", "") or "")[:5]
            return (
                street,
                (address.get("city", "") or "").strip().upper(),
                (address.get("state", "") or "").strip().upper(),
                postal_code,
            )
    return ("", "", "", "")


def _token_overlap(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens))


def _name_match_score(candidate_names: set[str], organization_name: str) -> tuple[int, str]:
    org_standardized = standardize_alias_tokens(organization_name)

    for candidate_name in candidate_names:
        if candidate_name == org_standardized:
            return 3, "Exact standardized match against the official NPI organization name."

    for candidate_name in candidate_names:
        if min(len(candidate_name), len(org_standardized)) >= 14 and (
            candidate_name.startswith(org_standardized) or org_standardized.startswith(candidate_name)
        ):
            return 2, "Prefix-style standardized match against the official NPI organization name."

    for candidate_name in candidate_names:
        if _token_overlap(candidate_name, org_standardized) >= 0.85:
            return 1, "High token-overlap match against the official NPI organization name."

    return 0, ""


def _taxonomy_score(result: dict) -> tuple[int, str]:
    _, taxonomy_desc = _primary_taxonomy(result)
    upper_desc = taxonomy_desc.upper()
    if any(keyword in upper_desc for keyword in FACILITY_TAXONOMY_KEYWORDS):
        return 2, taxonomy_desc
    return 0, taxonomy_desc


def _taxonomy_priority(candidate_name: str, taxonomy_desc: str) -> int:
    upper_candidate = candidate_name.upper()
    upper_taxonomy = taxonomy_desc.upper()

    if "HOSPICE" in upper_candidate and "HOSPICE" not in upper_taxonomy:
        return -1
    if "HOSPITAL" in upper_candidate and "HOSPITAL" not in upper_taxonomy and "GENERAL ACUTE CARE" not in upper_taxonomy:
        return -1
    if "MEDICAL CENTER" in upper_candidate and not any(
        keyword in upper_taxonomy for keyword in {"HOSPITAL", "GENERAL ACUTE CARE", "CLINIC/CENTER", "REHABILITATION"}
    ):
        return -1
    if "CLINIC" in upper_candidate and "CLINIC/CENTER" not in upper_taxonomy:
        return -1
    if "HEALTH SYSTEM" in upper_candidate and not any(
        keyword in upper_taxonomy for keyword in {"HOSPITAL", "GENERAL ACUTE CARE", "PSYCHIATRIC HOSPITAL", "HOSPICE"}
    ):
        return -1

    for keyword, score in FACILITY_TAXONOMY_PRIORITY:
        if keyword in upper_taxonomy:
            return score
    return 0


def verify_npi_facilities() -> None:
    candidate_path = _doh_candidate_path()
    if not candidate_path.exists():
        raise SystemExit(
            f"Missing DOH verification candidates at {candidate_path}. Run the WA doh_verification_candidates pipeline first."
        )

    with candidate_path.open(encoding="utf-8") as handle:
        candidates = [
            row
            for row in csv.DictReader(handle)
            if row["verification_status"] == "candidate_only" and _is_facility_like(row["canonical_recipient_name"])
        ]

    candidates = sorted(candidates, key=lambda item: float(item["total_amount"]), reverse=True)
    max_candidates = int(os.getenv("PFIP_NPI_VERIFY_LIMIT", DEFAULT_MAX_CANDIDATES_PER_RUN))
    candidates = candidates[:max_candidates]
    alias_index = _load_aliases()

    matched_rows: list[dict[str, str]] = []
    audit_rows: list[dict[str, str]] = []

    for candidate in candidates:
        candidate_names = {
            standardize_alias_tokens(name)
            for name in _search_terms(candidate, alias_index)
        }

        best_match: dict[str, str] | None = None
        best_score = -1
        best_rank_tuple: tuple[int, int, int, int, int] = (-1, -1, -1, -1, -1)
        best_match_count = 0
        seen_best_signatures: set[tuple[str, str, str, str]] = set()

        for search_name in _search_terms(candidate, alias_index):
            response = _query_npi(search_name)
            results = response.get("results", [])

            if not results:
                audit_rows.append(
                    {
                        "canonical_recipient_id": candidate["canonical_recipient_id"],
                        "canonical_recipient_name": candidate["canonical_recipient_name"],
                        "search_name": search_name,
                        "npi_number": "",
                        "organization_name": "",
                        "taxonomy_code": "",
                        "taxonomy_desc": "",
                        "location_address": "",
                        "match_status": "no_results",
                        "match_explanation": "Official CMS NPI Registry returned no organization results for this search.",
                    }
                )
                continue

            for result in results:
                basic = result.get("basic", {})
                org_name = basic.get("organization_name", "")
                name_score, name_explanation = _name_match_score(candidate_names, org_name)
                taxonomy_score, taxonomy_desc = _taxonomy_score(result)
                priority_score = _taxonomy_priority(candidate["canonical_recipient_name"], taxonomy_desc)
                total_score = name_score + taxonomy_score + max(priority_score, 0)
                taxonomy_code, _ = _primary_taxonomy(result)
                location_address = _location_address(result)
                location_signature = _location_signature(result)
                organizational_subpart = (basic.get("organizational_subpart", "") or "").upper()
                subpart_priority = 1 if organizational_subpart == "NO" else 0
                address_quality = 1 if location_signature[0] and location_signature[3] else 0

                audit_rows.append(
                    {
                        "canonical_recipient_id": candidate["canonical_recipient_id"],
                        "canonical_recipient_name": candidate["canonical_recipient_name"],
                        "search_name": search_name,
                        "npi_number": result.get("number", ""),
                        "organization_name": org_name,
                        "taxonomy_code": taxonomy_code,
                        "taxonomy_desc": taxonomy_desc,
                        "location_address": location_address,
                        "match_status": "candidate_result",
                        "match_explanation": name_explanation
                        if name_score
                        else "Returned by official CMS NPI Registry but did not meet name-match rules.",
                    }
                )

                if basic.get("status") != "A" or name_score == 0 or taxonomy_score == 0 or priority_score < 0:
                    continue

                rank_tuple = (name_score, priority_score, taxonomy_score, subpart_priority, address_quality)
                if rank_tuple > best_rank_tuple:
                    best_score = total_score
                    best_rank_tuple = rank_tuple
                    best_match_count = 1
                    seen_best_signatures = {location_signature}
                    best_match = {
                        "canonical_recipient_id": candidate["canonical_recipient_id"],
                        "state_code": STATE_CODE,
                        "source_slug": SOURCE_SLUG,
                        "canonical_recipient_name": candidate["canonical_recipient_name"],
                        "canonical_name_standardized": candidate["canonical_name_standardized"],
                        "verification_status": "matched",
                        "verification_route": "cms_npi_registry_facility_match",
                        "match_explanation": name_explanation,
                        "search_name": search_name,
                        "npi_number": result.get("number", ""),
                        "organization_name": org_name,
                        "organization_status": basic.get("status", ""),
                        "organizational_subpart": organizational_subpart,
                        "enumeration_date": basic.get("enumeration_date", ""),
                        "last_updated_epoch": basic.get("last_updated_epoch", ""),
                        "taxonomy_code": taxonomy_code,
                        "taxonomy_desc": taxonomy_desc,
                        "location_address": location_address,
                        "source_url_primary": NPI_API_PAGE_URL,
                        "source_url_secondary": candidate["source_url_primary"],
                        "total_amount": candidate["total_amount"],
                        "payment_count": candidate["payment_count"],
                        "top_agency": candidate["top_agency"],
                        "primary_focus_area": candidate["primary_focus_area"],
                        "focus_areas": candidate["focus_areas"],
                    }
                elif rank_tuple == best_rank_tuple:
                    if location_signature not in seen_best_signatures:
                        seen_best_signatures.add(location_signature)
                        best_match_count += 1

        if best_match and best_match_count == 1:
            matched_rows.append(best_match)
        elif best_match:
            audit_rows.append(
                {
                    "canonical_recipient_id": candidate["canonical_recipient_id"],
                    "canonical_recipient_name": candidate["canonical_recipient_name"],
                    "search_name": best_match["search_name"],
                    "npi_number": best_match["npi_number"],
                    "organization_name": best_match["organization_name"],
                    "taxonomy_code": best_match["taxonomy_code"],
                    "taxonomy_desc": best_match["taxonomy_desc"],
                    "location_address": best_match["location_address"],
                    "match_status": "ambiguous_exact_facility_match",
                    "match_explanation": (
                        "Multiple active facility-like NPI results tied for the top-ranked facility match, so no single NPI was assigned automatically."
                    ),
                }
            )

    output_dir = _normalized_dir()
    match_path = output_dir / "npi_facility_verified_matches.csv"
    audit_path = output_dir / "npi_facility_search_audit.csv"

    with match_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "canonical_recipient_id",
            "state_code",
            "source_slug",
            "canonical_recipient_name",
            "canonical_name_standardized",
            "verification_status",
            "verification_route",
            "match_explanation",
            "search_name",
            "npi_number",
            "organization_name",
            "organization_status",
            "organizational_subpart",
            "enumeration_date",
            "last_updated_epoch",
            "taxonomy_code",
            "taxonomy_desc",
            "location_address",
            "source_url_primary",
            "source_url_secondary",
            "total_amount",
            "payment_count",
            "top_agency",
            "primary_focus_area",
            "focus_areas",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in matched_rows:
            writer.writerow(row)

    with audit_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "canonical_recipient_id",
            "canonical_recipient_name",
            "search_name",
            "npi_number",
            "organization_name",
            "taxonomy_code",
            "taxonomy_desc",
            "location_address",
            "match_status",
            "match_explanation",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(row)

    print(f"Facility-like candidates searched: {len(candidates)}")
    print(f"Verified NPI facility matches: {len(matched_rows)}")
    print(f"Verified match CSV: {match_path}")
    print(f"Search audit CSV: {audit_path}")
