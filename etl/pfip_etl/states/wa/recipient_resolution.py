from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from pfip_etl.io import ensure_directory
from pfip_etl.states.wa.common import standardize_alias_tokens

STATE_CODE = "WA"
SOURCE_SLUG = "open_checkbook"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _recipient_rollup_path() -> Path:
    return _normalized_dir() / "recipient_rollups.csv"


def _is_prefix_variant(left: str, right: str) -> bool:
    if left == right:
        return True
    shorter, longer = sorted((left, right), key=len)
    if len(shorter) < 12:
        return False
    return longer.startswith(shorter)


def _resolution_bucket(row: dict[str, str]) -> tuple[str, str]:
    standardized = standardize_alias_tokens(row["vendor_name_normalized"])
    return (row["state_code"], standardized)


def _match_method(group: list[dict[str, str]]) -> tuple[str, str]:
    unique_normalized = {row["vendor_name_normalized"] for row in group}
    if len(unique_normalized) == 1:
        return (
            "exact_standardized_name",
            "Single normalized name matched directly after standardizing known suffix and state-token variants.",
        )

    if all(
        _is_prefix_variant(row["vendor_name_normalized"], next(iter(unique_normalized)))
        or _is_prefix_variant(next(iter(unique_normalized)), row["vendor_name_normalized"])
        for row in group
    ):
        return (
            "truncation_or_abbreviation_variant",
            "Merged aliases because names share the same standardized core and differ only by workbook truncation or trailing state/corporate variants.",
        )

    return (
        "standardized_name_group",
        "Merged aliases because names collapsed to the same standardized canonical form within the same focus area.",
    )


def build_recipient_resolution() -> None:
    input_path = _recipient_rollup_path()
    if not input_path.exists():
        raise SystemExit(
            f"Missing recipient rollups at {input_path}. Run the WA open checkbook rollups first."
        )

    with input_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_resolution_bucket(row)].append(row)

    canonical_rows: list[dict[str, str]] = []
    alias_rows: list[dict[str, str]] = []

    for (_state_code, standardized_name), group in sorted(grouped.items()):
        canonical_name = max(
            group,
            key=lambda row: (len(row["vendor_name_example"]), float(row["total_amount"])),
        )["vendor_name_example"]
        total_amount = sum(float(row["total_amount"]) for row in group)
        payment_count = sum(int(row["payment_count"]) for row in group)
        active_month_count = max(int(row["active_month_count"]) for row in group)
        focus_area_counter = Counter(row["focus_area"] for row in group)
        agency_counter = Counter(row["top_agency"] for row in group)
        category_counter = Counter(row["top_category"] for row in group)
        subcategory_counter = Counter(row["top_subcategory"] for row in group)
        alias_examples = sorted({row["vendor_name_example"] for row in group})
        resolution_method, resolution_explanation = _match_method(group)
        canonical_recipient_id = str(
            uuid5(
                NAMESPACE_URL,
                f"pfip:{STATE_CODE}:{SOURCE_SLUG}:{standardized_name}",
            )
        )

        canonical_rows.append(
            {
                "canonical_recipient_id": canonical_recipient_id,
                "state_code": STATE_CODE,
                "source_slug": SOURCE_SLUG,
                "primary_focus_area": focus_area_counter.most_common(1)[0][0],
                "focus_area_count": str(len(focus_area_counter)),
                "canonical_recipient_name": canonical_name,
                "canonical_name_standardized": standardized_name,
                "resolution_method": resolution_method,
                "resolution_explanation": resolution_explanation,
                "alias_count": str(len(group)),
                "payment_count": str(payment_count),
                "total_amount": f"{total_amount:.2f}",
                "top_agency": agency_counter.most_common(1)[0][0],
                "top_category": category_counter.most_common(1)[0][0],
                "top_subcategory": subcategory_counter.most_common(1)[0][0],
                "active_month_count": str(active_month_count),
                "focus_areas": " | ".join(
                    f"{focus_area}:{count}" for focus_area, count in focus_area_counter.most_common()
                ),
                "alias_examples": " | ".join(alias_examples[:10]),
            }
        )

        for row in group:
            alias_rows.append(
                {
                    "canonical_recipient_id": canonical_recipient_id,
                    "state_code": STATE_CODE,
                    "source_slug": SOURCE_SLUG,
                    "source_focus_area": row["focus_area"],
                    "canonical_name_standardized": standardized_name,
                    "canonical_recipient_name": canonical_name,
                    "source_vendor_name_example": row["vendor_name_example"],
                    "source_vendor_name_normalized": row["vendor_name_normalized"],
                    "source_total_amount": row["total_amount"],
                    "source_payment_count": row["payment_count"],
                    "source_top_agency": row["top_agency"],
                    "resolution_method": resolution_method,
                    "resolution_explanation": resolution_explanation,
                }
            )

    output_dir = _normalized_dir()

    canonical_path = output_dir / "canonical_recipients.csv"
    with canonical_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(canonical_rows[0].keys()))
        writer.writeheader()
        for row in sorted(
            canonical_rows,
            key=lambda item: (float(item["total_amount"]), int(item["payment_count"])),
            reverse=True,
        ):
            writer.writerow(row)

    alias_path = output_dir / "recipient_alias_links.csv"
    with alias_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(alias_rows[0].keys()))
        writer.writeheader()
        for row in sorted(
            alias_rows,
            key=lambda item: (
                item["canonical_name_standardized"],
                -float(item["source_total_amount"]),
                item["source_vendor_name_normalized"],
            ),
        ):
            writer.writerow(row)

    print(f"Input rollups: {len(rows)}")
    print(f"Canonical recipients: {len(canonical_rows)}")
    print(f"Alias links: {len(alias_rows)}")
    print(f"Canonical CSV: {canonical_path}")
    print(f"Alias CSV: {alias_path}")
