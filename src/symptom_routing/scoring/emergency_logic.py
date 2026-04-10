from __future__ import annotations

from src.symptom_routing.utils.parsing import normalize_text, to_sorted_unique


STRONG_EMERGENCY_FLAGS = {
    "chest pain": {"chest pain", "douleur thoracique"},
    "severe difficulty breathing": {
        "severe difficulty breathing",
        "cannot breathe",
        "hard to breathe",
        "difficulte respiratoire severe",
        "n arrive pas a respirer",
    },
    "stroke symptoms": {
        "stroke symptoms",
        "stroke like",
        "numb face",
        "slurred speech",
        "face droop",
        "symptomes d avc",
        "engourdissement du visage",
        "difficulte a parler",
        "visage affaisse",
    },
    "seizure": {"seizure", "convulsion", "active seizure"},
    "loss of consciousness": {
        "loss of consciousness",
        "fainted and unresponsive",
        "perte de conscience",
        "inconscient",
    },
    "severe bleeding": {"severe bleeding", "heavy bleeding", "saignement severe"},
    "suicidal ideation": {"suicidal ideation", "want to die", "ideation suicidaire"},
    "anaphylaxis": {"anaphylaxis", "anaphylaxie"},
    "severe allergic reaction": {
        "severe allergic reaction",
        "lip swelling",
        "tongue swelling",
        "reaction allergique severe",
        "gonflement des levres",
    },
    "cyanosis": {"cyanosis", "cyanose", "blue lips", "lips turning blue", "levres bleues"},
    "major trauma": {"major trauma", "traumatisme majeur", "high speed crash"},
    "unresponsive child": {"unresponsive child", "enfant inconscient"},
    "high-risk infant symptoms": {
        "high risk infant symptoms",
        "infant fever",
        "poor feeding",
        "hard to wake",
        "symptomes a haut risque chez le nourrisson",
        "fievre chez le nourrisson",
        "difficile a reveiller",
    },
}

SERIOUS_CONCERN_MARKERS = {
    "shortness of breath",
    "essoufflement",
    "cannot walk",
    "incapable de marcher",
    "worsening swelling",
    "confusion",
}

MILD_CONCERN_MARKERS = {
    "worsening",
    "getting worse",
    "empire",
    "aggrave",
    "persistent fever",
    "fievre persistante",
}

RESUSCITATION_RED_FLAGS = {
    "loss of consciousness",
    "cyanosis",
    "unresponsive child",
}

EMERGENT_RED_FLAGS = {
    "chest pain",
    "severe difficulty breathing",
    "stroke symptoms",
    "seizure",
    "severe bleeding",
    "suicidal ideation",
    "anaphylaxis",
    "severe allergic reaction",
    "major trauma",
    "high-risk infant symptoms",
}


def detect_emergency_flags(text: str, age_group: str) -> list[str]:
    normalized = normalize_text(text)
    matches: list[str] = []
    for label, phrases in STRONG_EMERGENCY_FLAGS.items():
        if any(normalize_text(phrase) in normalized for phrase in phrases):
            matches.append(label)

    if age_group == "infant":
        if "fever" in normalized or "fievre" in normalized:
            matches.append("high-risk infant symptoms")
        if "hard to wake" in normalized or "difficile a reveiller" in normalized:
            matches.append("high-risk infant symptoms")

    return to_sorted_unique(matches)


def red_flag_component(text: str, emergency_flags: list[str]) -> int:
    normalized = normalize_text(text)
    if len(emergency_flags) >= 2:
        return 100
    if emergency_flags:
        return 50
    if any(marker in normalized for marker in SERIOUS_CONCERN_MARKERS):
        return 50
    if any(marker in normalized for marker in MILD_CONCERN_MARKERS):
        return 15
    return 0


def is_resuscitation_flag(flag: str) -> bool:
    return flag in RESUSCITATION_RED_FLAGS


def is_emergent_flag(flag: str) -> bool:
    return flag in EMERGENT_RED_FLAGS
