from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from pfip_etl.io import download_binary, ensure_directory, file_sha256, utc_now
from pfip_etl.models import PaymentRawRecord, SourceRunManifest

WASHINGTON_OPEN_CHECKBOOK_URL = "https://fiscal.wa.gov/Spending/VendorPayments2527.xlsx"
SOURCE_SLUG = "open_checkbook"
STATE_CODE = "WA"
XML_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _read_shared_strings(workbook_path: Path) -> list[str]:
    with zipfile.ZipFile(workbook_path) as archive:
        if "xl/sharedStrings.xml" not in archive.namelist():
            return []

        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        values: list[str] = []
        for item in root.findall("a:si", XML_NS):
            text = "".join(node.text or "" for node in item.iterfind(".//a:t", XML_NS))
            values.append(text)
        return values


def _sheet_targets(workbook_path: Path) -> list[tuple[str, str]]:
    with zipfile.ZipFile(workbook_path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}

        targets: list[tuple[str, str]] = []
        for sheet in workbook.find("a:sheets", XML_NS):
            rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            targets.append((sheet.attrib["name"], f"xl/{rel_map[rel_id]}"))
        return targets


def _iter_sheet_rows(workbook_path: Path, sheet_target: str, shared_strings: list[str]) -> list[list[str]]:
    with zipfile.ZipFile(workbook_path) as archive:
        worksheet = ET.fromstring(archive.read(sheet_target))
        rows = worksheet.findall(".//a:sheetData/a:row", XML_NS)
        parsed_rows: list[list[str]] = []
        for row in rows:
            values: list[str] = []
            for cell in row.findall("a:c", XML_NS):
                raw_value = cell.find("a:v", XML_NS)
                if raw_value is None:
                    values.append("")
                    continue

                value = raw_value.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared_strings[int(value)]
                values.append(value.strip())
            parsed_rows.append(values)
        return parsed_rows


def _build_manifest(workbook_path: Path, source_url: str) -> SourceRunManifest:
    return SourceRunManifest(
        state_code=STATE_CODE,
        source_slug=SOURCE_SLUG,
        source_url=source_url,
        local_path=str(workbook_path),
        retrieved_at=utc_now(),
        sha256=file_sha256(workbook_path),
    )


def parse_open_checkbook_workbook(
    workbook_path: Path,
    source_url: str = WASHINGTON_OPEN_CHECKBOOK_URL,
) -> tuple[SourceRunManifest, list[PaymentRawRecord]]:
    manifest = _build_manifest(workbook_path, source_url)
    shared_strings = _read_shared_strings(workbook_path)
    records: list[PaymentRawRecord] = []

    for sheet_name, sheet_target in _sheet_targets(workbook_path):
        rows = _iter_sheet_rows(workbook_path, sheet_target, shared_strings)
        if not rows:
            continue

        for row_index, row in enumerate(rows[1:], start=2):
            if len(row) < 11:
                continue
            if not any(row):
                continue

            records.append(
                PaymentRawRecord(
                    state_code=STATE_CODE,
                    source_slug=SOURCE_SLUG,
                    biennium=row[0],
                    fiscal_year=int(row[1]),
                    fiscal_month=int(row[2]),
                    agency_code=row[3],
                    agency_name=row[4].strip(),
                    object_code=row[5],
                    category_name=row[6].strip(),
                    subobject_code=row[7],
                    subcategory_name=row[8].strip(),
                    vendor_name_raw=row[9].strip(),
                    amount=float(row[10]),
                    source_url=source_url,
                    source_sheet=sheet_name,
                    source_row_number=row_index,
                    retrieved_at=manifest.retrieved_at,
                    source_file_sha256=manifest.sha256,
                )
            )

    return manifest, records


def pull_washington_open_checkbook() -> None:
    run_dir = ensure_directory(_data_root() / "raw" / "wa" / SOURCE_SLUG)
    workbook_path = run_dir / "VendorPayments2527.xlsx"
    download_binary(WASHINGTON_OPEN_CHECKBOOK_URL, workbook_path)

    manifest, records = parse_open_checkbook_workbook(workbook_path)

    manifest_path = run_dir / "VendorPayments2527.manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    csv_path = run_dir / "VendorPayments2527.payments.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(PaymentRawRecord.model_fields.keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(record.model_dump(mode="json"))

    sample_path = run_dir / "VendorPayments2527.sample.json"
    sample_payload = [record.model_dump(mode="json") for record in records[:25]]
    sample_path.write_text(json.dumps(sample_payload, indent=2), encoding="utf-8")

    print(f"Downloaded workbook: {workbook_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Parsed payment rows: {len(records)}")
    print(f"CSV output: {csv_path}")
    print(f"Sample JSON: {sample_path}")
