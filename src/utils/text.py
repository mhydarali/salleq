from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timezone

from unidecode import unidecode


NON_ALNUM = re.compile(r"[^a-z0-9]+")
TIME_HH_MM = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*$")
NUMBER_RE = re.compile(r"(-?\d+(?:\.\d+)?)")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    lowered = unidecode(value).lower()
    collapsed = NON_ALNUM.sub(" ", lowered)
    return re.sub(r"\s+", " ", collapsed).strip()


def normalize_identifier(value: str | None) -> str:
    return NON_ALNUM.sub("_", normalize_text(value)).strip("_")


def parse_metric_int(value: str | None) -> int | None:
    if not value:
        return None
    match = NUMBER_RE.search(value.replace(",", "."))
    if not match:
        return None
    return int(float(match.group(1)))


def parse_metric_pct(value: str | None) -> float | None:
    parsed = parse_metric_int(value)
    if parsed is None:
        return None
    return float(parsed)


def parse_duration_to_minutes(value: str | None) -> int | None:
    if not value:
        return None
    if match := TIME_HH_MM.match(value):
        hours = int(match.group(1))
        minutes = int(match.group(2))
        return hours * 60 + minutes
    parsed = parse_metric_int(value)
    return parsed


def parse_duration_to_hours_from_text(text: str) -> float:
    cleaned = normalize_text(text)
    if not cleaned:
        return 0.0
    if "day" in cleaned or "jour" in cleaned:
        match = NUMBER_RE.search(cleaned)
        if match:
            return round(float(match.group(1)) * 24, 2)
    if "week" in cleaned or "semaine" in cleaned:
        match = NUMBER_RE.search(cleaned)
        if match:
            return round(float(match.group(1)) * 24 * 7, 2)
    if "hour" in cleaned or "heure" in cleaned:
        match = NUMBER_RE.search(cleaned)
        if match:
            return round(float(match.group(1)), 2)
    if "minute" in cleaned or "min" in cleaned:
        match = NUMBER_RE.search(cleaned)
        if match:
            return round(float(match.group(1)) / 60.0, 2)
    return 0.0


def haversine_km(lat1: float | None, lon1: float | None, lat2: float | None, lon2: float | None) -> float | None:
    if None in (lat1, lon1, lat2, lon2):
        return None
    radius_km = 6371.0
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    d_phi = math.radians(float(lat2) - float(lat1))
    d_lambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return round(radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)
