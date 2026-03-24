from __future__ import annotations

import csv
import json
import math
import re
import ssl
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"
GEOCODER_SOURCE_URL = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
GEOCODER_BENCHMARK = "4"
GEOCODER_VINTAGE = "4"
PROXIMITY_CLUSTER_KM = 0.2


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _read_csv(name: str) -> list[dict[str, str]]:
    path = _normalized_dir() / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ssl_context():
    return ssl._create_unverified_context()


def _clean_address(value: str) -> str:
    cleaned = (value or "").replace("<br>", ", ").replace("<br/>", ", ").replace("<br />", ", ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace(" ,", ",").strip(" ,")
    return cleaned


def _normalize_address(value: str) -> str:
    cleaned = _clean_address(value).upper()
    cleaned = re.sub(r"[^A-Z0-9,\s#&/-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s*,\s*", ", ", cleaned)
    return cleaned.strip(" ,")


def _extract_city_state_zip(normalized_address: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in normalized_address.split(",") if part.strip()]
    if len(parts) < 2:
        return "", "", ""
    if len(parts) >= 3:
        state_zip_match = re.match(r"^([A-Z]{2})\s+(\d{5})(?:-\d{4})?$", parts[-1])
        if state_zip_match:
            return parts[-2], state_zip_match.group(1), state_zip_match.group(2)
    if len(parts) >= 4 and re.fullmatch(r"[A-Z]{2}", parts[-2]):
        zip_match = re.match(r"^(\d{5})(?:-\d{4})?$", parts[-1])
        if zip_match:
            return parts[-3], parts[-2], zip_match.group(1)
    compact_zip_match = re.match(r"^(\d{5})(\d{4})$", parts[-1])
    if len(parts) >= 4 and re.fullmatch(r"[A-Z]{2}", parts[-2]) and compact_zip_match:
        return parts[-3], parts[-2], compact_zip_match.group(1)
    return "", "", ""


def _parse_matched_address(value: str) -> tuple[str, str, str]:
    parts = [part.strip().upper() for part in value.split(",") if part.strip()]
    if len(parts) < 3:
        return "", "", ""

    city = parts[-2]
    state_zip_match = re.match(r"^([A-Z]{2})\s+(\d{5})(?:-\d{4})?$", parts[-1])
    if not state_zip_match:
        return "", "", ""
    return city, state_zip_match.group(1), state_zip_match.group(2)


def _geocode_address(address: str) -> dict[str, str]:
    params = urlencode(
        {
            "address": address,
            "benchmark": GEOCODER_BENCHMARK,
            "vintage": GEOCODER_VINTAGE,
            "format": "json",
        }
    )
    request = Request(
        f"{GEOCODER_SOURCE_URL}?{params}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urlopen(request, timeout=30, context=_ssl_context()) as response:  # nosec: official public source
        payload = json.loads(response.read().decode("utf-8", errors="replace"))

    matches = payload.get("result", {}).get("addressMatches", [])
    if not matches:
        return {
            "geocode_status": "no_match",
            "matched_address": "",
            "longitude": "",
            "latitude": "",
            "census_tiger_line_id": "",
            "county_name": "",
            "county_fips": "",
            "state_fips": "",
        }

    match = matches[0]
    county = (match.get("geographies", {}).get("Counties") or [{}])[0]
    return {
        "geocode_status": "matched",
        "matched_address": match.get("matchedAddress", ""),
        "longitude": str(match.get("coordinates", {}).get("x", "")),
        "latitude": str(match.get("coordinates", {}).get("y", "")),
        "census_tiger_line_id": match.get("tigerLine", {}).get("tigerLineId", ""),
        "county_name": county.get("NAME", ""),
        "county_fips": county.get("GEOID", ""),
        "state_fips": county.get("STATE", ""),
    }


def _unique_site_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        if row["link_status"] != "verified":
            continue
        if not row["source_record_location"]:
            continue
        cleaned_address = _clean_address(row["source_record_location"])
        normalized_address = _normalize_address(cleaned_address)
        if not normalized_address:
            continue

        key = (row["canonical_recipient_id"], row["source_system"], normalized_address)
        if key not in grouped:
            city, state, zip_code = _extract_city_state_zip(normalized_address)
            grouped[key] = {
                "canonical_recipient_id": row["canonical_recipient_id"],
                "state_code": row["state_code"],
                "source_slug": row["source_slug"],
                "sector": row["sector"],
                "source_system": row["source_system"],
                "identifier_type": row["identifier_type"],
                "identifier_value": row["identifier_value"],
                "identifier_display": row["identifier_display"],
                "canonical_recipient_name": row["identifier_display"],
                "source_record_name": row["source_record_name"],
                "source_record_status": row["source_record_status"],
                "raw_address": cleaned_address,
                "normalized_address": normalized_address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "county_name": "",
                "county_fips": "",
                "source_url_primary": row["source_url_primary"],
                "source_url_secondary": row["source_url_secondary"],
                "total_amount": row["total_amount"],
                "payment_count": row["payment_count"],
                "top_agency": row["top_agency"],
                "primary_focus_area": row["primary_focus_area"],
                "focus_areas": row["focus_areas"],
                "identifier_count": "1",
            }
        else:
            grouped[key]["identifier_count"] = str(int(grouped[key]["identifier_count"]) + 1)
    return list(grouped.values())


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _cluster_by_proximity(rows: list[dict[str, str]]) -> dict[int, list[int]]:
    geocoded_indices = [
        index
        for index, row in enumerate(rows)
        if row["geocode_status"] == "matched" and row["latitude"] and row["longitude"]
    ]
    parent = {index: index for index in geocoded_indices}

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for pos, left_index in enumerate(geocoded_indices):
        left_row = rows[left_index]
        lat1 = float(left_row["latitude"])
        lon1 = float(left_row["longitude"])
        for right_index in geocoded_indices[pos + 1 :]:
            right_row = rows[right_index]
            lat2 = float(right_row["latitude"])
            lon2 = float(right_row["longitude"])
            if _haversine_km(lat1, lon1, lat2, lon2) <= PROXIMITY_CLUSTER_KM:
                union(left_index, right_index)

    clusters: dict[int, list[int]] = defaultdict(list)
    for index in geocoded_indices:
        clusters[find(index)].append(index)
    return clusters


def build_geo_enrichment() -> None:
    identifier_rows = _read_csv("recipient_identifier_links.csv")
    site_rows = _unique_site_rows(identifier_rows)

    geocode_cache: dict[str, dict[str, str]] = {}
    for row in site_rows:
        geocode_cache[row["normalized_address"]] = _geocode_address(row["normalized_address"])

    enriched_rows: list[dict[str, str]] = []
    exact_clusters: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in site_rows:
        geocode_result = geocode_cache[row["normalized_address"]]
        city = row["city"]
        state = row["state"]
        zip_code = row["zip_code"]
        if geocode_result.get("matched_address") and not (city and state and zip_code):
            fallback_city, fallback_state, fallback_zip = _parse_matched_address(
                geocode_result["matched_address"]
            )
            city = city or fallback_city
            state = state or fallback_state
            zip_code = zip_code or fallback_zip
        enriched_row = row | geocode_result
        enriched_row["city"] = city
        enriched_row["state"] = state
        enriched_row["zip_code"] = zip_code
        enriched_row["county_name"] = geocode_result.get("county_name", "")
        enriched_row["county_fips"] = geocode_result.get("county_fips", "")
        enriched_rows.append(enriched_row)
        exact_clusters[row["normalized_address"]].append(enriched_row)

    proximity_clusters = _cluster_by_proximity(enriched_rows)
    proximity_cluster_ids: dict[int, str] = {}
    for cluster_number, (root_index, members) in enumerate(
        sorted(proximity_clusters.items(), key=lambda item: len(item[1]), reverse=True),
        start=1,
    ):
        cluster_id = f"wa_geo_cluster_{cluster_number:04d}"
        for member in members:
            proximity_cluster_ids[member] = cluster_id

    point_rows: list[dict[str, str]] = []
    for index, row in enumerate(enriched_rows):
        exact_cluster_size = len(exact_clusters[row["normalized_address"]])
        point_rows.append(
            row
            | {
                "exact_address_cluster_id": f"wa_exact_{abs(hash(row['normalized_address'])) % 10_000_000:07d}",
                "exact_address_cluster_size": str(exact_cluster_size),
                "proximity_cluster_id": proximity_cluster_ids.get(index, ""),
            }
        )

    cluster_rows: list[dict[str, str]] = []
    for normalized_address, members in exact_clusters.items():
        if len(members) < 2:
            continue
        cluster_rows.append(
            {
                "cluster_type": "exact_address",
                "cluster_id": f"wa_exact_{abs(hash(normalized_address)) % 10_000_000:07d}",
                "cluster_size": str(len(members)),
                "normalized_address": normalized_address,
                "city": members[0]["city"],
                "state": members[0]["state"],
                "zip_code": members[0]["zip_code"],
                "latitude": members[0]["latitude"],
                "longitude": members[0]["longitude"],
                "recipient_names": " | ".join(sorted({member["source_record_name"] for member in members})),
                "source_systems": " | ".join(sorted({member["source_system"] for member in members})),
            }
        )

    for cluster_id in sorted(set(proximity_cluster_ids.values())):
        members = [
            point_rows[index]
            for index, value in proximity_cluster_ids.items()
            if value == cluster_id
        ]
        if len(members) < 2:
            continue
        avg_lat = sum(float(member["latitude"]) for member in members) / len(members)
        avg_lon = sum(float(member["longitude"]) for member in members) / len(members)
        cluster_rows.append(
            {
                "cluster_type": "proximity",
                "cluster_id": cluster_id,
                "cluster_size": str(len(members)),
                "normalized_address": "",
                "city": members[0]["city"],
                "state": members[0]["state"],
                "zip_code": members[0]["zip_code"],
                "latitude": f"{avg_lat:.6f}",
                "longitude": f"{avg_lon:.6f}",
                "recipient_names": " | ".join(sorted({member["source_record_name"] for member in members})),
                "source_systems": " | ".join(sorted({member["source_system"] for member in members})),
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "features": [],
    }
    for row in point_rows:
        if row["geocode_status"] != "matched" or not row["latitude"] or not row["longitude"]:
            continue
        geojson["features"].append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["longitude"]), float(row["latitude"])],
                },
                "properties": {
                    "canonical_recipient_id": row["canonical_recipient_id"],
                    "source_record_name": row["source_record_name"],
                    "source_system": row["source_system"],
                    "sector": row["sector"],
                    "normalized_address": row["normalized_address"],
                    "exact_address_cluster_id": row["exact_address_cluster_id"],
                    "exact_address_cluster_size": row["exact_address_cluster_size"],
                    "proximity_cluster_id": row["proximity_cluster_id"],
                    "total_amount": row["total_amount"],
                    "payment_count": row["payment_count"],
                    "top_agency": row["top_agency"],
                    "primary_focus_area": row["primary_focus_area"],
                    "county_name": row["county_name"],
                    "county_fips": row["county_fips"],
                },
            }
        )

    output_dir = _normalized_dir()
    points_path = output_dir / "recipient_geo_points.csv"
    clusters_path = output_dir / "recipient_geo_clusters.csv"
    geojson_path = output_dir / "recipient_geo_points.geojson"
    summary_path = output_dir / "recipient_geo_summary.json"

    point_fieldnames = [
        "canonical_recipient_id",
        "state_code",
        "source_slug",
        "sector",
        "source_system",
        "identifier_type",
        "identifier_value",
        "identifier_display",
        "canonical_recipient_name",
        "source_record_name",
        "source_record_status",
        "raw_address",
        "normalized_address",
        "city",
        "state",
        "zip_code",
        "county_name",
        "county_fips",
        "state_fips",
        "geocode_status",
        "matched_address",
        "longitude",
        "latitude",
        "census_tiger_line_id",
        "exact_address_cluster_id",
        "exact_address_cluster_size",
        "proximity_cluster_id",
        "source_url_primary",
        "source_url_secondary",
        "total_amount",
        "payment_count",
        "top_agency",
        "primary_focus_area",
        "focus_areas",
        "identifier_count",
    ]
    with points_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=point_fieldnames)
        writer.writeheader()
        for row in point_rows:
            writer.writerow(row)

    cluster_fieldnames = [
        "cluster_type",
        "cluster_id",
        "cluster_size",
        "normalized_address",
        "city",
        "state",
        "zip_code",
        "latitude",
        "longitude",
        "recipient_names",
        "source_systems",
    ]
    with clusters_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=cluster_fieldnames)
        writer.writeheader()
        for row in sorted(cluster_rows, key=lambda item: int(item["cluster_size"]), reverse=True):
            writer.writerow(row)

    geojson_path.write_text(json.dumps(geojson, indent=2), encoding="utf-8")

    summary = {
        "state_code": STATE_CODE,
        "source_slug": SOURCE_SLUG,
        "unique_verified_sites": len(point_rows),
        "geocoded_site_count": sum(1 for row in point_rows if row["geocode_status"] == "matched"),
        "exact_address_cluster_count": sum(1 for row in cluster_rows if row["cluster_type"] == "exact_address"),
        "proximity_cluster_count": sum(1 for row in cluster_rows if row["cluster_type"] == "proximity"),
        "cluster_radius_km": PROXIMITY_CLUSTER_KM,
        "geocoder_source_url": GEOCODER_SOURCE_URL,
        "methodology_notes": [
            "Only verified recipient identifiers with an address were included in the geo layer.",
            "Coordinates and county assignments are from the official U.S. Census geocoder using the current public benchmark and geography vintage.",
            "Exact-address clusters group records with the same normalized address; proximity clusters group points within 0.2 km.",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Unique verified sites: {len(point_rows)}")
    print(f"Geocoded site count: {summary['geocoded_site_count']}")
    print(f"Geo points CSV: {points_path}")
    print(f"Geo clusters CSV: {clusters_path}")
    print(f"GeoJSON: {geojson_path}")
    print(f"Geo summary JSON: {summary_path}")
