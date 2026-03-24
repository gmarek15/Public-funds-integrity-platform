from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pfip_etl.io import ensure_directory
from pfip_etl.states.wa.common import standardize_alias_tokens

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"
DEFAULT_MAX_CANDIDATES_PER_RUN = 50

SOS_SEARCH_PAGE_URL = "https://ccfs.sos.wa.gov/ng-app/view/businesssearch/searchBusiness.html"
SOS_APP_URL = "https://ccfs.sos.wa.gov/#/BusinessSearch"
SOS_BUSINESS_SEARCH_URL = "https://ccfs-api.prod.sos.wa.gov/api/BusinessSearch/GetBusinessSearchDetails"
SOS_BUSINESS_INFO_URL = "https://ccfs-api.prod.sos.wa.gov/api/BusinessSearch/BusinessInformation"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _candidate_path() -> Path:
    return _normalized_dir() / "sos_ubi_candidates.csv"


def _alias_path() -> Path:
    return _normalized_dir() / "recipient_alias_links.csv"


def _load_aliases() -> dict[str, list[str]]:
    alias_index: dict[str, list[str]] = {}
    with _alias_path().open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            alias_index.setdefault(row["canonical_recipient_id"], []).append(row["source_vendor_name_example"])
    return alias_index


def _search_terms(candidate: dict[str, str], alias_index: dict[str, list[str]]) -> list[str]:
    terms: list[str] = [candidate["canonical_recipient_name"]]
    terms.extend(alias_index.get(candidate["canonical_recipient_id"], []))
    terms.extend(
        alias.strip()
        for alias in candidate.get("alias_examples", "").split("|")
        if alias.strip()
    )

    seen: set[str] = set()
    deduped: list[str] = []
    for term in terms:
        cleaned = " ".join(term.split()).strip()
        if not cleaned:
            continue
        key = cleaned.upper()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
    return deduped


def _search_payload(query: str) -> bytes:
    payload = {
        "Type": "businessname",
        "ID": query,
        "IsSearch": "true",
        "PageID": "1",
        "PageCount": "10",
        "BusinessTypeId": "0",
        "IsOnline": "true",
        "SearchType": "",
        "isSearchClick": "true",
        "SortBy": "BusinessName",
        "SortType": "ASC",
    }
    return urlencode(payload).encode("utf-8")


def _post_search(query: str, turnstile_token: str) -> list[dict]:
    request = Request(
        SOS_BUSINESS_SEARCH_URL,
        data=_search_payload(query),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "X-reCAPTCHA": turnstile_token,
            "Referer": SOS_APP_URL,
            "Origin": "https://ccfs.sos.wa.gov",
        },
    )
    with urlopen(request, timeout=30) as response:  # nosec: official public source
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _get_business_info(business_id: str, turnstile_token: str) -> dict:
    request = Request(
        f"{SOS_BUSINESS_INFO_URL}?businessID={business_id}",
        headers={
            "User-Agent": "Mozilla/5.0",
            "X-reCAPTCHA": turnstile_token,
            "Referer": SOS_APP_URL,
            "Origin": "https://ccfs.sos.wa.gov",
        },
    )
    with urlopen(request, timeout=30) as response:  # nosec: official public source
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _nested_get(data: dict, *keys: str) -> str:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    if current is None:
        return ""
    return str(current)


def _token_overlap(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens))


def _match_business(candidate: dict[str, str], aliases: list[str], business_info: dict) -> tuple[bool, str]:
    candidate_names = [candidate["canonical_recipient_name"], *aliases]
    candidate_names_standardized = {standardize_alias_tokens(name) for name in candidate_names if name}

    business_name = business_info.get("BusinessName", "")
    dba_name = business_info.get("DBABusinessName", "")
    business_standardized = standardize_alias_tokens(business_name)
    dba_standardized = standardize_alias_tokens(dba_name) if dba_name else ""

    if business_standardized in candidate_names_standardized:
        return True, "Exact standardized match against the official SOS business name."

    if dba_standardized and dba_standardized in candidate_names_standardized:
        return True, "Exact standardized match against the official SOS DBA name."

    for candidate_name in candidate_names_standardized:
        if not candidate_name:
            continue
        if (
            min(len(candidate_name), len(business_standardized)) >= 14
            and (candidate_name.startswith(business_standardized) or business_standardized.startswith(candidate_name))
        ):
            return True, "Prefix-style standardized match against the official SOS business name."
        if dba_standardized and min(len(candidate_name), len(dba_standardized)) >= 14 and (
            candidate_name.startswith(dba_standardized) or dba_standardized.startswith(candidate_name)
        ):
            return True, "Prefix-style standardized match against the official SOS DBA name."
        if _token_overlap(candidate_name, business_standardized) >= 0.85:
            return True, "High token-overlap match against the official SOS business name."

    return False, ""


def verify_sos_ubi_matches() -> None:
    turnstile_token = os.getenv("PFIP_WA_SOS_TURNSTILE_TOKEN", "").strip()
    if not turnstile_token:
        raise SystemExit(
            "Missing PFIP_WA_SOS_TURNSTILE_TOKEN. Open the official SOS business search in a browser, "
            "complete the Turnstile verification, capture the public token used for the search requests, "
            "and rerun this pipeline."
        )

    candidate_path = _candidate_path()
    alias_path = _alias_path()
    if not candidate_path.exists():
        raise SystemExit(
            f"Missing SOS UBI candidates at {candidate_path}. Run the WA sos_ubi_candidates pipeline first."
        )
    if not alias_path.exists():
        raise SystemExit(
            f"Missing recipient alias links at {alias_path}. Run the WA recipient resolution pipeline first."
        )

    with candidate_path.open(encoding="utf-8") as handle:
        candidates = [
            row
            for row in csv.DictReader(handle)
            if row["candidate_route"] == "sos_business_entity_review"
        ]

    candidates = sorted(candidates, key=lambda item: float(item["total_amount"]), reverse=True)
    max_candidates = int(os.getenv("PFIP_WA_SOS_VERIFY_LIMIT", DEFAULT_MAX_CANDIDATES_PER_RUN))
    candidates = candidates[:max_candidates]
    alias_index = _load_aliases()

    matched_rows: list[dict[str, str]] = []
    audit_rows: list[dict[str, str]] = []

    for candidate in candidates:
        search_terms = _search_terms(candidate, alias_index)
        candidate_aliases = alias_index.get(candidate["canonical_recipient_id"], [])
        matched = False

        for search_name in search_terms:
            try:
                results = _post_search(search_name, turnstile_token)
            except HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                raise SystemExit(
                    f"SOS search failed with HTTP {exc.code}. Response excerpt: {error_body[:200]}"
                ) from exc

            if not results:
                audit_rows.append(
                    {
                        "canonical_recipient_id": candidate["canonical_recipient_id"],
                        "canonical_recipient_name": candidate["canonical_recipient_name"],
                        "search_name": search_name,
                        "business_id": "",
                        "matched_business_name": "",
                        "matched_dba_name": "",
                        "ubi_number": "",
                        "business_status": "",
                        "business_type": "",
                        "principal_office_address": "",
                        "match_status": "no_results",
                        "match_explanation": "Official SOS business search returned no results for this query.",
                    }
                )
                continue

            for result in results[:10]:
                business_id = str(result.get("BusinessID", ""))
                if not business_id:
                    continue

                try:
                    business_info = _get_business_info(business_id, turnstile_token)
                except HTTPError as exc:
                    error_body = exc.read().decode("utf-8", errors="replace")
                    raise SystemExit(
                        f"SOS business information lookup failed with HTTP {exc.code}. Response excerpt: {error_body[:200]}"
                    ) from exc

                is_match, explanation = _match_business(candidate, candidate_aliases, business_info)
                audit_row = {
                    "canonical_recipient_id": candidate["canonical_recipient_id"],
                    "canonical_recipient_name": candidate["canonical_recipient_name"],
                    "search_name": search_name,
                    "business_id": business_id,
                    "matched_business_name": business_info.get("BusinessName", ""),
                    "matched_dba_name": business_info.get("DBABusinessName", ""),
                    "ubi_number": business_info.get("UBINumber", ""),
                    "business_status": business_info.get("BusinessStatus", ""),
                    "business_type": business_info.get("BusinessType", ""),
                    "principal_office_address": _nested_get(
                        business_info,
                        "PrincipalOffice",
                        "PrincipalStreetAddress",
                        "FullAddress",
                    ),
                    "match_status": "matched" if is_match else "searched_not_matched",
                    "match_explanation": explanation
                    if is_match
                    else "Returned by official SOS search but did not meet strict recipient-to-business matching rules.",
                }
                audit_rows.append(audit_row)

                if not is_match:
                    continue

                matched_rows.append(
                    {
                        "canonical_recipient_id": candidate["canonical_recipient_id"],
                        "state_code": STATE_CODE,
                        "source_slug": SOURCE_SLUG,
                        "canonical_recipient_name": candidate["canonical_recipient_name"],
                        "canonical_name_standardized": candidate["canonical_name_standardized"],
                        "verification_status": "matched",
                        "candidate_route": candidate["candidate_route"],
                        "match_explanation": explanation,
                        "search_name": search_name,
                        "business_id": business_id,
                        "official_business_name": business_info.get("BusinessName", ""),
                        "official_dba_name": business_info.get("DBABusinessName", ""),
                        "ubi_number": business_info.get("UBINumber", ""),
                        "business_type": business_info.get("BusinessType", ""),
                        "business_status": business_info.get("BusinessStatus", ""),
                        "jurisdiction": business_info.get("JurisdictionDesc", ""),
                        "formation_date": business_info.get("DateOfIncorporation", ""),
                        "next_annual_report_due_date": business_info.get("NextARDueDate", ""),
                        "inactive_date": business_info.get("InActiveDate", ""),
                        "nature_of_business": business_info.get("BINAICSCodeDesc", ""),
                        "agent_name": result.get("AgentName", ""),
                        "principal_office_address": _nested_get(
                            business_info,
                            "PrincipalOffice",
                            "PrincipalStreetAddress",
                            "FullAddress",
                        ),
                        "principal_mailing_address": _nested_get(
                            business_info,
                            "PrincipalOffice",
                            "PrincipalMailingAddress",
                            "FullAddress",
                        ),
                        "source_url_search_page": SOS_SEARCH_PAGE_URL,
                        "source_url_search_endpoint": SOS_BUSINESS_SEARCH_URL,
                        "source_url_business_information_endpoint": SOS_BUSINESS_INFO_URL,
                        "total_amount": candidate["total_amount"],
                        "payment_count": candidate["payment_count"],
                        "top_agency": candidate["top_agency"],
                        "primary_focus_area": candidate["primary_focus_area"],
                        "focus_areas": candidate["focus_areas"],
                    }
                )
                matched = True
                break

            if matched:
                break

    output_dir = _normalized_dir()
    match_path = output_dir / "sos_ubi_verified_matches.csv"
    audit_path = output_dir / "sos_ubi_search_audit.csv"

    with match_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "canonical_recipient_id",
            "state_code",
            "source_slug",
            "canonical_recipient_name",
            "canonical_name_standardized",
            "verification_status",
            "candidate_route",
            "match_explanation",
            "search_name",
            "business_id",
            "official_business_name",
            "official_dba_name",
            "ubi_number",
            "business_type",
            "business_status",
            "jurisdiction",
            "formation_date",
            "next_annual_report_due_date",
            "inactive_date",
            "nature_of_business",
            "agent_name",
            "principal_office_address",
            "principal_mailing_address",
            "source_url_search_page",
            "source_url_search_endpoint",
            "source_url_business_information_endpoint",
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
            "business_id",
            "matched_business_name",
            "matched_dba_name",
            "ubi_number",
            "business_status",
            "business_type",
            "principal_office_address",
            "match_status",
            "match_explanation",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(row)

    print(f"Candidates searched: {len(candidates)}")
    print(f"Verified SOS/UBI matches: {len(matched_rows)}")
    print(f"Verified match CSV: {match_path}")
    print(f"Search audit CSV: {audit_path}")
