from __future__ import annotations

import csv
import json
import os
import re
import ssl
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from pfip_etl.io import ensure_directory
from pfip_etl.states.wa.common import standardize_alias_tokens

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"
SEARCH_BASE_URL = "https://www.findchildcarewa.org/PSS_Search?q="
REMOTE_URL = "https://www.findchildcarewa.org/apexremote"
DEFAULT_MAX_CANDIDATES_PER_RUN = 40


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _candidate_path() -> Path:
    return _normalized_dir() / "dcyf_childcare_candidates.csv"


def _ssl_context():
    return ssl._create_unverified_context()


def _extract_method_meta(page_html: str, method_name: str) -> dict[str, str]:
    match = re.search(
        r'\{"name":"' + re.escape(method_name) + r'".*?"csrf":"([^"]+)".*?"authorization":"([^"]+)"',
        page_html,
    )
    if not match:
        raise RuntimeError(f"Could not find remoting metadata for {method_name}")
    return {"csrf": match.group(1), "authorization": match.group(2)}


def _fetch_search_page(query: str) -> tuple[str, str, dict[str, dict[str, str]]]:
    url = SEARCH_BASE_URL + quote(query)
    with urlopen(url, timeout=30, context=_ssl_context()) as response:  # nosec: official public source
        html = response.read().decode("utf-8", errors="replace")
    vid = re.search(r'"vid":"([^"]+)"', html)
    if not vid:
        raise RuntimeError("Could not find Visualforce remoting page id")
    methods = {
        "getSOSLKeys": _extract_method_meta(html, "getSOSLKeys"),
        "queryProviders": _extract_method_meta(html, "queryProviders"),
    }
    return url, vid.group(1), methods


def _remote_call(
    *,
    referer_url: str,
    vid: str,
    methods: dict[str, dict[str, str]],
    method_name: str,
    data: list,
    tid: int,
):
    payload = {
        "action": "PSS_SearchController",
        "method": method_name,
        "data": data,
        "type": "rpc",
        "tid": tid,
        "ctx": {"csrf": methods[method_name]["csrf"], "vid": vid, "ns": "", "ver": 39},
    }
    request = Request(
        REMOTE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer_url,
            "Origin": "https://www.findchildcarewa.org",
        },
    )
    with urlopen(request, timeout=30, context=_ssl_context()) as response:  # nosec: official public source
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _extract_business_name(label: str) -> str:
    if "(" in label and ")" in label:
        inner = label.split("(", 1)[1].rsplit(")", 1)[0].strip()
        if inner:
            return inner
    return label.strip()


def _token_overlap(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens))


def _match_provider(candidate_name: str, provider: dict) -> tuple[bool, str]:
    canonical = standardize_alias_tokens(candidate_name)
    display_label = provider.get("Account_Name_Display_Label__c", "")
    business_name = _extract_business_name(display_label)
    business_standardized = standardize_alias_tokens(business_name)

    if canonical == business_standardized:
        return True, "Exact standardized match against the provider business name shown in Child Care Check."

    if canonical.startswith(business_standardized) or business_standardized.startswith(canonical):
        if min(len(canonical), len(business_standardized)) >= 12:
            return True, "Prefix-style standardized match against the provider business name shown in Child Care Check."

    if _token_overlap(canonical, business_standardized) >= 0.8:
        return True, "High token-overlap match against the provider business name shown in Child Care Check."

    return False, ""


def verify_dcyf_childcare_matches() -> None:
    candidate_path = _candidate_path()
    if not candidate_path.exists():
        raise SystemExit(
            f"Missing DCYF childcare candidates at {candidate_path}. Run the candidate pipeline first."
        )

    with candidate_path.open(encoding="utf-8") as handle:
        candidates = [
            row
            for row in csv.DictReader(handle)
            if row["verification_route"] == "child_care_check_licensing_review"
        ]

    candidates = sorted(candidates, key=lambda item: float(item["total_amount"]), reverse=True)
    max_candidates = int(os.getenv("PFIP_DCYF_VERIFY_LIMIT", DEFAULT_MAX_CANDIDATES_PER_RUN))
    candidates = candidates[:max_candidates]

    matched_rows: list[dict[str, str]] = []
    audit_rows: list[dict[str, str]] = []

    for index, candidate in enumerate(candidates, start=1):
        query = candidate["search_name"]
        search_url, vid, methods = _fetch_search_page(query)

        id_response = _remote_call(
            referer_url=search_url,
            vid=vid,
            methods=methods,
            method_name="getSOSLKeys",
            data=[query, None, ["DEL Licensed"], [], None, None, None, []],
            tid=100 + index,
        )
        provider_ids = id_response[0].get("result", [])
        providers = []
        if provider_ids:
            provider_response = _remote_call(
                referer_url=search_url,
                vid=vid,
                methods=methods,
                method_name="queryProviders",
                data=[provider_ids[:10]],
                tid=1000 + index,
            )
            providers = provider_response[0].get("result", [])

        matched = False
        for provider in providers:
            is_match, explanation = _match_provider(candidate["canonical_recipient_name"], provider)
            audit_rows.append(
                {
                    "canonical_recipient_id": candidate["canonical_recipient_id"],
                    "canonical_recipient_name": candidate["canonical_recipient_name"],
                    "search_name": query,
                    "search_url": search_url,
                    "provider_record_id": provider.get("Id", ""),
                    "provider_display_name": provider.get("Account_Name_Display_Label__c", ""),
                    "provider_business_name": _extract_business_name(provider.get("Account_Name_Display_Label__c", "")),
                    "facility_type": provider.get("Latest_License_Facility_Type_Name__c", ""),
                    "license_status": provider.get("Latest_License_Status__c", ""),
                    "provider_location": provider.get("Provider_Location_Label__c", ""),
                    "license_record_id": provider.get("Latest_License_Rec_ID__c", ""),
                    "subsidy_participation": str(provider.get("Subsidy_Participation__c", "")),
                    "eceap_funded": str(provider.get("Is_Funded_ECEAP__c", "")),
                    "head_start_funded": str(provider.get("Is_Funded_HS__c", "")),
                    "early_head_start_funded": str(provider.get("Is_Funded_EHS__c", "")),
                    "match_status": "matched" if is_match else "searched_not_matched",
                    "match_explanation": explanation if is_match else "Returned by official Child Care Check search but did not meet strict business-name match rules.",
                }
            )
            if is_match:
                matched = True
                matched_rows.append(
                    {
                        "canonical_recipient_id": candidate["canonical_recipient_id"],
                        "state_code": STATE_CODE,
                        "source_slug": SOURCE_SLUG,
                        "canonical_recipient_name": candidate["canonical_recipient_name"],
                        "canonical_name_standardized": candidate["canonical_name_standardized"],
                        "verification_status": "matched",
                        "verification_route": candidate["verification_route"],
                        "match_explanation": explanation,
                        "search_url": search_url,
                        "provider_record_id": provider.get("Id", ""),
                        "provider_display_name": provider.get("Account_Name_Display_Label__c", ""),
                        "provider_business_name": _extract_business_name(provider.get("Account_Name_Display_Label__c", "")),
                        "provider_location": provider.get("Provider_Location_Label__c", ""),
                        "facility_type": provider.get("Latest_License_Facility_Type_Name__c", ""),
                        "license_status": provider.get("Latest_License_Status__c", ""),
                        "license_record_id": provider.get("Latest_License_Rec_ID__c", ""),
                        "subsidy_participation": str(provider.get("Subsidy_Participation__c", "")),
                        "eceap_funded": str(provider.get("Is_Funded_ECEAP__c", "")),
                        "head_start_funded": str(provider.get("Is_Funded_HS__c", "")),
                        "early_head_start_funded": str(provider.get("Is_Funded_EHS__c", "")),
                        "source_url_primary": candidate["source_url_primary"],
                        "source_url_secondary": candidate["source_url_secondary"],
                        "source_url_program": candidate["source_url_program"],
                        "source_url_complaints": candidate["source_url_complaints"],
                        "total_amount": candidate["total_amount"],
                        "payment_count": candidate["payment_count"],
                        "top_agency": candidate["top_agency"],
                    }
                )
                break

        if not providers:
            audit_rows.append(
                {
                    "canonical_recipient_id": candidate["canonical_recipient_id"],
                    "canonical_recipient_name": candidate["canonical_recipient_name"],
                    "search_name": query,
                    "search_url": search_url,
                    "provider_record_id": "",
                    "provider_display_name": "",
                    "provider_business_name": "",
                    "facility_type": "",
                    "license_status": "",
                    "provider_location": "",
                    "license_record_id": "",
                    "subsidy_participation": "",
                    "eceap_funded": "",
                    "head_start_funded": "",
                    "early_head_start_funded": "",
                    "match_status": "no_results",
                    "match_explanation": "Official Child Care Check search returned no provider records for this query.",
                }
            )
        elif not matched:
            pass

    output_dir = _normalized_dir()
    match_path = output_dir / "dcyf_childcare_verified_matches.csv"
    audit_path = output_dir / "dcyf_childcare_search_audit.csv"

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
            "search_url",
            "provider_record_id",
            "provider_display_name",
            "provider_business_name",
            "provider_location",
            "facility_type",
            "license_status",
            "license_record_id",
            "subsidy_participation",
            "eceap_funded",
            "head_start_funded",
            "early_head_start_funded",
            "source_url_primary",
            "source_url_secondary",
            "source_url_program",
            "source_url_complaints",
            "total_amount",
            "payment_count",
            "top_agency",
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
            "search_url",
            "provider_record_id",
            "provider_display_name",
            "provider_business_name",
            "facility_type",
            "license_status",
            "provider_location",
            "license_record_id",
            "subsidy_participation",
            "eceap_funded",
            "head_start_funded",
            "early_head_start_funded",
            "match_status",
            "match_explanation",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(row)

    print(f"Candidates searched: {len(candidates)}")
    print(f"Verified matches: {len(matched_rows)}")
    print(f"Verified match CSV: {match_path}")
    print(f"Search audit CSV: {audit_path}")
