from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rapidfuzz import fuzz

from src.utils.text import normalize_text


@dataclass
class MasterFacility:
    facility_id_normalized: str
    facility_name: str
    full_address: str
    city: str


@dataclass
class MatchResult:
    matched_facility_id: str | None
    matched_facility_name: str | None
    match_confidence: float
    match_method: str


def match_live_facility(
    facility_name_raw: str,
    address_raw: str,
    candidates: Iterable[MasterFacility],
) -> MatchResult:
    normalized_name = normalize_text(facility_name_raw)
    normalized_address = normalize_text(address_raw)

    best_score = -1.0
    best_candidate: MasterFacility | None = None

    for candidate in candidates:
        name_score = fuzz.token_set_ratio(normalized_name, normalize_text(candidate.facility_name))
        address_score = fuzz.token_set_ratio(normalized_address, normalize_text(candidate.full_address))
        city_score = 100 if candidate.city and normalize_text(candidate.city) in normalized_address else 0
        composite = 0.55 * name_score + 0.30 * address_score + 0.15 * city_score
        if composite > best_score:
            best_score = composite
            best_candidate = candidate

    if not best_candidate:
        return MatchResult(None, None, 0.0, "no_match")

    method = "exactish" if best_score >= 95 else "fuzzy"
    return MatchResult(
        matched_facility_id=best_candidate.facility_id_normalized,
        matched_facility_name=best_candidate.facility_name,
        match_confidence=round(best_score / 100.0, 4),
        match_method=method,
    )
