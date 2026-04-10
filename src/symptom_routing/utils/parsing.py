from __future__ import annotations

import re
import unicodedata
from typing import Iterable


LANGUAGE_HINTS = {
    "fr": {
        "depuis",
        "douleur",
        "fievre",
        "essoufflement",
        "gorge",
        "cheville",
        "enfant",
        "nourrisson",
        "respirer",
        "heure",
        "jours",
        "naus",
        "avec",
        "apres",
        "situation",
        "semble",
        "moment",
        "gonflement",
    },
    "en": {
        "since",
        "pain",
        "fever",
        "ankle",
        "throat",
        "breathing",
        "hours",
        "days",
        "swelling",
        "child",
        "infant",
        "with",
        "after",
        "stable",
        "patient",
        "worse",
        "today",
    },
}

AGE_GROUP_ALIASES = {
    "baby": "infant",
    "bebe": "infant",
    "bébé": "infant",
    "infant": "infant",
    "nourrisson": "infant",
    "child": "child",
    "kid": "child",
    "enfant": "child",
    "adult": "adult",
    "adulte": "adult",
    "older adult": "older_adult",
    "older_adult": "older_adult",
    "senior": "older_adult",
    "aine": "older_adult",
    "aîné": "older_adult",
}

SYMPTOM_CATEGORY_KEYWORDS = {
    "respiratory": {
        "breath",
        "breathing",
        "wheeze",
        "cough",
        "respir",
        "essoufflement",
        "asthma",
    },
    "cardiac": {
        "chest pain",
        "chest tightness",
        "thorac",
        "palpitation",
        "heart",
    },
    "neurological": {
        "stroke",
        "slurred speech",
        "weakness",
        "numb",
        "headache",
        "migraine",
        "seizure",
        "avc",
        "engour",
        "confusion",
    },
    "digestive": {
        "abdominal",
        "stomach",
        "vomit",
        "nausea",
        "diarrhea",
        "abdomen",
        "naus",
        "vom",
        "diarrh",
    },
    "infection": {
        "fever",
        "ear pain",
        "sore throat",
        "throat",
        "feverish",
        "fievre",
        "gorge",
        "infection",
        "urinary",
    },
    "injury": {
        "ankle",
        "cut",
        "bleeding",
        "fall",
        "wrist",
        "sprain",
        "injury",
        "cheville",
        "entorse",
        "coupure",
        "blessure",
    },
    "immune": {
        "allergic",
        "allergy",
        "rash",
        "hives",
        "anaphyl",
        "allerg",
        "eruption",
        "urticaire",
    },
}

PRIMARY_SYMPTOM_PATTERNS = (
    "chest pain",
    "shortness of breath",
    "stroke-like symptoms",
    "severe bleeding",
    "allergic reaction",
    "abdominal pain",
    "headache",
    "ear pain",
    "sore throat",
    "twisted ankle",
    "minor cut",
    "rash",
    "fever",
    "vomiting",
    "back pain",
    "wrist pain",
    "wheezing",
)

SEVERITY_PATTERNS = {
    "severe pain": {"severe pain", "douleur severe", "douleur intense"},
    "impaired function": {
        "cannot walk",
        "unable to walk",
        "incapable de marcher",
        "cannot use arm",
        "trouble speaking",
    },
    "worsening": {
        "worsening",
        "getting worse",
        "empire",
        "aggrave",
        "worse today",
    },
    "moderate pain": {
        "swelling",
        "gonflement",
        "moderate pain",
        "fever",
        "fievre",
        "painful",
        "tender",
    },
}


def normalize_text(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text or "")
    ascii_text = stripped.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def detect_language(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return "unknown"
    fr_score = sum(1 for hint in LANGUAGE_HINTS["fr"] if hint in normalized)
    en_score = sum(1 for hint in LANGUAGE_HINTS["en"] if hint in normalized)
    if fr_score == en_score == 0:
        return "unknown"
    return "fr" if fr_score > en_score else "en"


def coerce_age_group(age_group: str | None) -> str:
    if not age_group:
        return "unknown"
    normalized = normalize_text(age_group)
    return AGE_GROUP_ALIASES.get(normalized, "unknown")


def parse_duration_hours(text: str, explicit_duration_hours: int | None = None) -> int:
    if explicit_duration_hours is not None:
        return max(0, int(explicit_duration_hours))

    normalized = normalize_text(text)
    patterns = (
        (r"(\d+)\s*(hour|hours|hr|hrs|heure|heures|h)\b", 1),
        (r"(\d+)\s*(day|days|jour|jours)\b", 24),
        (r"(\d+)\s*(week|weeks|semaine|semaines)\b", 24 * 7),
    )
    for pattern, multiplier in patterns:
        match = re.search(pattern, normalized)
        if match:
            return int(match.group(1)) * multiplier
    if "since yesterday" in normalized or "depuis hier" in normalized:
        return 24
    if "today" in normalized or "aujourd hui" in normalized:
        return 6
    return 0


def extract_severity_indicators(text: str) -> list[str]:
    normalized = normalize_text(text)
    indicators: list[str] = []
    for label, phrases in SEVERITY_PATTERNS.items():
        if any(phrase in normalized for phrase in phrases):
            indicators.append(label)
    return sorted(set(indicators))


def infer_symptom_category(text: str) -> str:
    normalized = normalize_text(text)
    best_match = ("other", 0)
    for category, keywords in SYMPTOM_CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in normalized)
        if score > best_match[1]:
            best_match = (category, score)
    return best_match[0]


def infer_primary_symptom(text: str) -> str:
    normalized = normalize_text(text)
    for phrase in PRIMARY_SYMPTOM_PATTERNS:
        if normalize_text(phrase) in normalized:
            return phrase
    tokens = normalized.split()
    if not tokens:
        return "unspecified symptom"
    return " ".join(tokens[:4])


def to_sorted_unique(items: Iterable[str]) -> list[str]:
    return sorted({item for item in items if item})
