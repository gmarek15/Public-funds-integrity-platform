from __future__ import annotations

import io
import json
import ssl
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from pfip_etl.io import ensure_directory

STATE_CODE = "WA"
STATE_FIPS = "53"
SOURCE_SLUG = "open_checkbook"
COUNTY_KML_URL = "https://www2.census.gov/geo/tiger/GENZ2020/kml/cb_2020_us_county_20m.zip"
VIEWBOX_WIDTH = 1000
VIEWBOX_HEIGHT = 620


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _data_root() -> Path:
    return ensure_directory(_project_root() / "data")


def _normalized_dir() -> Path:
    return ensure_directory(_data_root() / "normalized" / "wa" / SOURCE_SLUG)


def _download_kml() -> bytes:
    request = Request(COUNTY_KML_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60, context=ssl._create_unverified_context()) as response:  # nosec
        return response.read()


def _parse_coordinates(raw: str) -> list[tuple[float, float]]:
    coordinates: list[tuple[float, float]] = []
    for chunk in raw.strip().split():
        lon, lat, *_ = chunk.split(",")
        coordinates.append((float(lon), float(lat)))
    return coordinates


def _extract_counties(payload: bytes) -> list[dict[str, object]]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        root = ET.fromstring(archive.read("cb_2020_us_county_20m.kml"))

    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    counties: list[dict[str, object]] = []
    for placemark in root.findall(".//kml:Placemark", ns):
        state_fp = placemark.findtext(".//kml:SimpleData[@name='STATEFP']", namespaces=ns)
        if state_fp != STATE_FIPS:
            continue
        county_name = placemark.findtext(".//kml:SimpleData[@name='NAME']", namespaces=ns) or ""
        geoid = placemark.findtext(".//kml:SimpleData[@name='GEOID']", namespaces=ns) or ""
        polygons = [
            _parse_coordinates(node.text or "")
            for node in placemark.findall(".//kml:Polygon//kml:outerBoundaryIs//kml:LinearRing//kml:coordinates", ns)
            if node.text
        ]
        if not polygons:
            continue
        counties.append(
            {
                "county_name": f"{county_name} County",
                "county_fips": geoid,
                "polygons": polygons,
            }
        )
    return counties


def _bounds(counties: list[dict[str, object]]) -> tuple[float, float, float, float]:
    all_points = [
        point
        for county in counties
        for polygon in county["polygons"]
        for point in polygon
    ]
    longitudes = [point[0] for point in all_points]
    latitudes = [point[1] for point in all_points]
    return min(longitudes), max(longitudes), min(latitudes), max(latitudes)


def _project_point(
    lon: float,
    lat: float,
    min_lon: float,
    max_lon: float,
    min_lat: float,
    max_lat: float,
) -> tuple[float, float]:
    x = ((lon - min_lon) / (max_lon - min_lon)) * VIEWBOX_WIDTH
    y = VIEWBOX_HEIGHT - ((lat - min_lat) / (max_lat - min_lat)) * VIEWBOX_HEIGHT
    return round(x, 2), round(y, 2)


def _path_from_polygon(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    commands = [f"M {points[0][0]} {points[0][1]}"]
    commands.extend(f"L {point[0]} {point[1]}" for point in points[1:])
    commands.append("Z")
    return " ".join(commands)


def build_county_boundaries() -> None:
    payload = _download_kml()
    counties = _extract_counties(payload)
    min_lon, max_lon, min_lat, max_lat = _bounds(counties)

    features: list[dict[str, object]] = []
    for county in counties:
        projected_polygons = [
            [
                _project_point(lon, lat, min_lon, max_lon, min_lat, max_lat)
                for lon, lat in polygon
            ]
            for polygon in county["polygons"]
        ]
        all_projected = [point for polygon in projected_polygons for point in polygon]
        centroid_x = sum(point[0] for point in all_projected) / len(all_projected)
        centroid_y = sum(point[1] for point in all_projected) / len(all_projected)
        features.append(
            {
                "county_name": county["county_name"],
                "county_fips": county["county_fips"],
                "svg_path": " ".join(_path_from_polygon(polygon) for polygon in projected_polygons),
                "label_x": round(centroid_x, 2),
                "label_y": round(centroid_y, 2),
            }
        )

    output = {
        "state_code": STATE_CODE,
        "source_url": COUNTY_KML_URL,
        "view_box": f"0 0 {VIEWBOX_WIDTH} {VIEWBOX_HEIGHT}",
        "bounds": {
            "min_lon": round(min_lon, 6),
            "max_lon": round(max_lon, 6),
            "min_lat": round(min_lat, 6),
            "max_lat": round(max_lat, 6),
        },
        "counties": sorted(features, key=lambda item: item["county_name"]),
    }
    output_path = _normalized_dir() / "washington_county_shapes.json"
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Washington county shapes JSON: {output_path}")
