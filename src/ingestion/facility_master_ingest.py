from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass

import httpx

from src.utils.text import now_utc_iso
from src.utils.text import normalize_identifier


@dataclass
class FacilityMasterRecord:
    index: str
    facility_name: str
    source_facility_type: str
    odhf_facility_type: str
    provider: str
    unit: str
    street_no: str
    street_name: str
    postal_code: str
    city: str
    province: str
    source_format_str_address: str
    csdname: str
    csduid: float | None
    pruid: int | None
    latitude: float | None
    longitude: float | None
    full_address: str
    facility_id_normalized: str
    is_quebec: bool
    ingested_at: str


EXPECTED_COLUMNS = {
    "facility_name": ["facility_name", "facility name", "name"],
    "source_facility_type": ["source_facility_type", "source facility type", "facility_type"],
    "odhf_facility_type": ["odhf_facility_type", "odhf facility type"],
    "provider": ["provider"],
    "unit": ["unit"],
    "street_no": ["street_no", "street number", "street_no_fr"],
    "street_name": ["street_name", "street name"],
    "postal_code": ["postal_code", "postal code"],
    "city": ["city"],
    "province": ["province"],
    "source_format_str_address": ["source_format_str_address", "full_address_source", "formatted_address"],
    "csdname": ["csdname"],
    "csduid": ["csduid"],
    "pruid": ["pruid"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lon", "lng"],
    "index": ["index", "id"],
}


def _resolve_column(fieldnames: list[str], aliases: list[str]) -> str | None:
    lowered = {name.lower(): name for name in fieldnames}
    for alias in aliases:
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return None


def _to_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _to_int(value: str | None) -> int | None:
    parsed = _to_float(value)
    return int(parsed) if parsed is not None else None


def load_facility_master(source_url: str) -> list[FacilityMasterRecord]:
    response = httpx.get(source_url, timeout=60.0, follow_redirects=True)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
        raw_csv = archive.read(csv_name)
        last_error: Exception | None = None
        for encoding in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                reader = csv.DictReader(io.StringIO(raw_csv.decode(encoding)))
                fieldnames = reader.fieldnames or []
                mapping = {key: _resolve_column(fieldnames, aliases) for key, aliases in EXPECTED_COLUMNS.items()}
                ingested_at = now_utc_iso()
                records: list[FacilityMasterRecord] = []
                for row in reader:
                    street_no = row.get(mapping["street_no"] or "", "")
                    street_name = row.get(mapping["street_name"] or "", "")
                    city = row.get(mapping["city"] or "", "")
                    postal_code = row.get(mapping["postal_code"] or "", "")
                    facility_name = row.get(mapping["facility_name"] or "", "")
                    full_address = ", ".join(part for part in [street_no, street_name, city, postal_code] if part).strip(", ")
                    records.append(
                        FacilityMasterRecord(
                            index=row.get(mapping["index"] or "", ""),
                            facility_name=facility_name,
                            source_facility_type=row.get(mapping["source_facility_type"] or "", ""),
                            odhf_facility_type=row.get(mapping["odhf_facility_type"] or "", ""),
                            provider=row.get(mapping["provider"] or "", ""),
                            unit=row.get(mapping["unit"] or "", ""),
                            street_no=street_no,
                            street_name=street_name,
                            postal_code=postal_code,
                            city=city,
                            province=row.get(mapping["province"] or "", ""),
                            source_format_str_address=row.get(mapping["source_format_str_address"] or "", ""),
                            csdname=row.get(mapping["csdname"] or "", ""),
                            csduid=_to_float(row.get(mapping["csduid"] or "", "")),
                            pruid=_to_int(row.get(mapping["pruid"] or "", "")),
                            latitude=_to_float(row.get(mapping["latitude"] or "", "")),
                            longitude=_to_float(row.get(mapping["longitude"] or "", "")),
                            full_address=full_address,
                            facility_id_normalized=normalize_identifier(f"{facility_name} {city} {postal_code}"),
                            is_quebec=(row.get(mapping["province"] or "", "").strip().upper() in {"QC", "QUEBEC", "QUÉBEC"}),
                            ingested_at=ingested_at,
                        )
                    )
                return records
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
        raise last_error or ValueError(f"Unable to decode facility master CSV from {source_url}")
