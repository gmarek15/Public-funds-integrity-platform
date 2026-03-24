from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"


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


def _parse_float(value: str) -> float:
    try:
        return float(value or "0")
    except ValueError:
        return 0.0


def _parse_int(value: str) -> int:
    try:
        return int(value or "0")
    except ValueError:
        return 0


def _join_sorted(values: set[str]) -> str:
    return " | ".join(sorted(value for value in values if value))


def _summarize_locations(
    point_rows: list[dict[str, str]],
    grouping_keys: tuple[str, ...],
) -> list[dict[str, str]]:
    grouped: dict[tuple[str, ...], dict[str, object]] = {}
    for row in point_rows:
        if row["geocode_status"] != "matched":
            continue
        key = tuple(row[key_name] for key_name in grouping_keys)
        if key not in grouped:
            grouped[key] = {
                "site_count": 0,
                "recipient_names": set(),
                "source_systems": set(),
                "focus_areas": set(),
                "sectors": set(),
                "top_agencies": set(),
                "total_amount": 0.0,
                "payment_count": 0,
            }
        entry = grouped[key]
        entry["site_count"] = int(entry["site_count"]) + 1
        entry["recipient_names"].add(row["canonical_recipient_name"])
        entry["source_systems"].add(row["source_system"])
        entry["focus_areas"].add(row["primary_focus_area"])
        entry["sectors"].add(row["sector"])
        entry["top_agencies"].add(row["top_agency"])
        entry["total_amount"] = float(entry["total_amount"]) + _parse_float(row["total_amount"])
        entry["payment_count"] = int(entry["payment_count"]) + _parse_int(row["payment_count"])

    summaries: list[dict[str, str]] = []
    for key, entry in sorted(
        grouped.items(),
        key=lambda item: (
            -float(item[1]["total_amount"]),
            -int(item[1]["site_count"]),
            item[0],
        ),
    ):
        row = {
            grouping_keys[index]: value
            for index, value in enumerate(key)
        }
        row |= {
            "site_count": str(entry["site_count"]),
            "recipient_count": str(len(entry["recipient_names"])),
            "total_amount": f"{float(entry['total_amount']):.2f}",
            "payment_count": str(entry["payment_count"]),
            "recipient_names": _join_sorted(entry["recipient_names"]),
            "source_systems": _join_sorted(entry["source_systems"]),
            "focus_areas": _join_sorted(entry["focus_areas"]),
            "sectors": _join_sorted(entry["sectors"]),
            "top_agencies": _join_sorted(entry["top_agencies"]),
        }
        summaries.append(row)
    return summaries


def _build_cluster_summary(
    point_rows: list[dict[str, str]],
    cluster_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    points_by_cluster: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in point_rows:
        if row["geocode_status"] != "matched":
            continue
        if row["exact_address_cluster_id"]:
            points_by_cluster[row["exact_address_cluster_id"]].append(row)
        if row["proximity_cluster_id"]:
            points_by_cluster[row["proximity_cluster_id"]].append(row)

    base_cluster_map = {row["cluster_id"]: row for row in cluster_rows}
    summaries: list[dict[str, str]] = []
    for cluster_id, base in sorted(
        base_cluster_map.items(),
        key=lambda item: (
            -_parse_int(item[1]["cluster_size"]),
            item[0],
        ),
    ):
        members = points_by_cluster.get(cluster_id, [])
        if len(members) < 2:
            continue
        total_amount = sum(_parse_float(member["total_amount"]) for member in members)
        payment_count = sum(_parse_int(member["payment_count"]) for member in members)
        summaries.append(
            {
                "cluster_id": cluster_id,
                "cluster_type": base["cluster_type"],
                "cluster_size": str(len(members)),
                "city": base["city"] or members[0]["city"],
                "state": base["state"] or members[0]["state"],
                "zip_code": base["zip_code"] or members[0]["zip_code"],
                "latitude": base["latitude"] or members[0]["latitude"],
                "longitude": base["longitude"] or members[0]["longitude"],
                "total_amount": f"{total_amount:.2f}",
                "payment_count": str(payment_count),
                "recipient_names": _join_sorted({member["canonical_recipient_name"] for member in members}),
                "source_systems": _join_sorted({member["source_system"] for member in members}),
                "focus_areas": _join_sorted({member["primary_focus_area"] for member in members}),
                "sectors": _join_sorted({member["sector"] for member in members}),
                "top_agencies": _join_sorted({member["top_agency"] for member in members}),
                "normalized_address": base["normalized_address"],
            }
        )
    return summaries


def _build_colocation_reviews(cluster_summaries: list[dict[str, str]]) -> list[dict[str, str]]:
    reviews: list[dict[str, str]] = []
    for row in cluster_summaries:
        if _parse_int(row["cluster_size"]) < 2:
            continue
        focus_areas = row["focus_areas"].split(" | ") if row["focus_areas"] else []
        distinct_focus_area_count = len([value for value in focus_areas if value])
        reviews.append(
            {
                "review_id": f"wa_colocation_review_{row['cluster_id']}",
                "state_code": STATE_CODE,
                "source_slug": SOURCE_SLUG,
                "review_type": "co_location_review",
                "review_status": "automated_review_only",
                "indicator_label": "Multiple verified recipient sites located together",
                "indicator_scope": row["cluster_type"],
                "cluster_id": row["cluster_id"],
                "cluster_type": row["cluster_type"],
                "cluster_size": row["cluster_size"],
                "city": row["city"],
                "state": row["state"],
                "zip_code": row["zip_code"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "recipient_names": row["recipient_names"],
                "source_systems": row["source_systems"],
                "focus_areas": row["focus_areas"],
                "sectors": row["sectors"],
                "top_agencies": row["top_agencies"],
                "total_amount": row["total_amount"],
                "payment_count": row["payment_count"],
                "review_priority": "medium" if distinct_focus_area_count > 1 else "low",
                "rationale": (
                    "This cluster groups verified recipient sites that share an address or fall within the "
                    "configured proximity threshold. Co-location can support operational review, but it does "
                    "not by itself indicate misconduct or an improper relationship."
                ),
                "methodology": (
                    "Built from verified provider or facility identifiers with source-backed addresses. "
                    "Exact-address clusters share the same normalized address. Proximity clusters group "
                    "geocoded points within 0.2 km."
                ),
                "source_traceability": (
                    "Derived from recipient_geo_points.csv and recipient_geo_clusters.csv, which are built "
                    "from official CMS NPI Registry, DCYF Child Care Check, and U.S. Census geocoder outputs."
                ),
            }
        )
    return reviews


def _build_county_summaries(point_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    summaries = _summarize_locations(point_rows, ("county_name", "county_fips", "state"))
    if not summaries:
        return []
    max_total_amount = max(_parse_float(row["total_amount"]) for row in summaries) or 1.0
    for row in summaries:
        total_amount = _parse_float(row["total_amount"])
        site_count = max(_parse_int(row["site_count"]), 1)
        row["spend_per_site"] = f"{(total_amount / site_count):.2f}"
        row["normalized_total_spend"] = f"{(total_amount / max_total_amount):.6f}"
    return summaries


def build_geo_rollups() -> None:
    point_rows = _read_csv("recipient_geo_points.csv")
    cluster_rows = _read_csv("recipient_geo_clusters.csv")
    if not point_rows:
        raise FileNotFoundError("recipient_geo_points.csv not found. Run geo_enrichment first.")

    city_summaries = _summarize_locations(point_rows, ("city", "state"))
    zip_summaries = _summarize_locations(point_rows, ("zip_code", "city", "state"))
    county_summaries = _build_county_summaries(point_rows)
    cluster_summaries = _build_cluster_summary(point_rows, cluster_rows)
    colocation_reviews = _build_colocation_reviews(cluster_summaries)

    output_dir = _normalized_dir()
    city_path = output_dir / "recipient_geo_city_summary.csv"
    zip_path = output_dir / "recipient_geo_zip_summary.csv"
    county_path = output_dir / "recipient_geo_county_summary.csv"
    cluster_summary_path = output_dir / "recipient_geo_cluster_summary.csv"
    review_path = output_dir / "recipient_colocation_reviews.csv"
    summary_path = output_dir / "recipient_geo_rollup_summary.json"

    city_fieldnames = [
        "city",
        "state",
        "site_count",
        "recipient_count",
        "total_amount",
        "payment_count",
        "recipient_names",
        "source_systems",
        "focus_areas",
        "sectors",
        "top_agencies",
    ]
    with city_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=city_fieldnames)
        writer.writeheader()
        writer.writerows(city_summaries)

    zip_fieldnames = [
        "zip_code",
        "city",
        "state",
        "site_count",
        "recipient_count",
        "total_amount",
        "payment_count",
        "recipient_names",
        "source_systems",
        "focus_areas",
        "sectors",
        "top_agencies",
    ]
    with zip_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=zip_fieldnames)
        writer.writeheader()
        writer.writerows(zip_summaries)

    county_fieldnames = [
        "county_name",
        "county_fips",
        "state",
        "site_count",
        "recipient_count",
        "total_amount",
        "payment_count",
        "spend_per_site",
        "normalized_total_spend",
        "recipient_names",
        "source_systems",
        "focus_areas",
        "sectors",
        "top_agencies",
    ]
    with county_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=county_fieldnames)
        writer.writeheader()
        writer.writerows(county_summaries)

    cluster_fieldnames = [
        "cluster_id",
        "cluster_type",
        "cluster_size",
        "city",
        "state",
        "zip_code",
        "latitude",
        "longitude",
        "total_amount",
        "payment_count",
        "recipient_names",
        "source_systems",
        "focus_areas",
        "sectors",
        "top_agencies",
        "normalized_address",
    ]
    with cluster_summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=cluster_fieldnames)
        writer.writeheader()
        writer.writerows(cluster_summaries)

    review_fieldnames = [
        "review_id",
        "state_code",
        "source_slug",
        "review_type",
        "review_status",
        "indicator_label",
        "indicator_scope",
        "cluster_id",
        "cluster_type",
        "cluster_size",
        "city",
        "state",
        "zip_code",
        "latitude",
        "longitude",
        "recipient_names",
        "source_systems",
        "focus_areas",
        "sectors",
        "top_agencies",
        "total_amount",
        "payment_count",
        "review_priority",
        "rationale",
        "methodology",
        "source_traceability",
    ]
    with review_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=review_fieldnames)
        writer.writeheader()
        writer.writerows(colocation_reviews)

    summary = {
        "state_code": STATE_CODE,
        "source_slug": SOURCE_SLUG,
        "city_summary_count": len(city_summaries),
        "zip_summary_count": len(zip_summaries),
        "county_summary_count": len(county_summaries),
        "cluster_summary_count": len(cluster_summaries),
        "co_location_review_count": len(colocation_reviews),
        "methodology_notes": [
            "Location summaries are built only from matched geocoded sites with verified recipient identifiers.",
            "Co-location reviews are automated review prompts, not findings of fraud or wrongdoing.",
            "Cluster summaries roll up the same source-backed sites used in recipient_geo_points.csv.",
        ],
        "source_files": [
            "recipient_geo_points.csv",
            "recipient_geo_clusters.csv",
            "recipient_geo_county_summary.csv",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"City summary CSV: {city_path}")
    print(f"ZIP summary CSV: {zip_path}")
    print(f"County summary CSV: {county_path}")
    print(f"Cluster summary CSV: {cluster_summary_path}")
    print(f"Co-location review CSV: {review_path}")
    print(f"Geo rollup summary JSON: {summary_path}")
