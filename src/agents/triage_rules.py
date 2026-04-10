from __future__ import annotations

from dataclasses import asdict, dataclass

from src.utils.text import normalize_text, parse_duration_to_hours_from_text


CTAS_LABELS = {
    1: "Resuscitation",
    2: "Emergent",
    3: "Urgent",
    4: "Less Urgent",
    5: "Non-Urgent",
}


RED_FLAG_GROUPS = {
    "chest_pain": ["chest pain", "douleur thoracique"],
    "severe_difficulty_breathing": ["difficulty breathing", "shortness of breath", "difficulte respiratoire", "essoufflement severe"],
    "stroke_symptoms": ["stroke", "avc", "face drooping", "slurred speech"],
    "seizure": ["seizure", "convulsion"],
    "loss_of_consciousness": ["loss of consciousness", "unconscious", "perte de conscience"],
    "severe_bleeding": ["severe bleeding", "heavy bleeding", "saignement important"],
    "suicidal_ideation": ["suicidal", "want to die", "suicidaire"],
    "anaphylaxis_signs": ["anaphylaxis", "throat swelling", "anaphylaxie"],
    "severe_allergic_reaction": ["severe allergic reaction", "reaction allergique"],
    "cyanosis": ["blue lips", "cyanosis", "cyanose"],
    "major_trauma": ["major trauma", "car crash", "traumatisme majeur"],
    "unresponsive_child": ["unresponsive child", "child not responding", "enfant inconscient"],
    "high_risk_infant_symptoms": ["infant fever", "fever under 3 months", "nourrisson"],
}


SYMPTOM_CATEGORIES = {
    "respiratory": ["cough", "fever", "breathing", "respiratoire", "dyspnea", "asthma"],
    "gastrointestinal": ["vomit", "vomiting", "nausea", "stomach", "abdominal", "diarrhea", "vomissements"],
    "musculoskeletal": ["sprain", "ankle", "back pain", "muscle", "joint", "entorse"],
    "neurological": ["headache", "migraine", "dizziness", "vertigo", "neurologique"],
    "dermatology": ["rash", "itch", "skin", "cut", "eczema", "eruption"],
    "mental_health": ["anxiety", "panic", "depression", "mental", "anxiete"],
}


SEVERITY_TERMS = {
    "severe": 2,
    "worst": 2,
    "cannot": 2,
    "unable": 2,
    "severe pain": 2,
    "mild": -1,
    "minor": -1,
    "slight": -1,
}


@dataclass
class TriageAssessment:
    language: str
    patient_age_group: str
    primary_symptom: str
    symptom_category: str
    duration_hours: float
    severity_indicators: list[str]
    emergency_flags: list[str]
    emergency_stop: bool
    provisional_ctas_level: int
    provisional_ctas_label: str
    recommended_facility_type: str
    recommended_urgency_band: str
    queue_eligible: bool
    reasoning_summary: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def detect_language(text: str) -> str:
    normalized = normalize_text(text)
    french_markers = {"bonjour", "douleur", "depuis", "respiratoire", "urgence", "nourrisson", "je"}
    if any(marker in normalized for marker in french_markers):
        return "fr"
    if normalized:
        return "en"
    return "unknown"


def categorize_symptom(text: str) -> str:
    normalized = normalize_text(text)
    for category, keywords in SYMPTOM_CATEGORIES.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "general"


def extract_primary_symptom(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return "unknown"
    return normalized.split(".")[0][:80]


def detect_severity_indicators(text: str) -> list[str]:
    normalized = normalize_text(text)
    indicators = [term for term in SEVERITY_TERMS if term in normalized]
    if "pain" in normalized or "douleur" in normalized:
        indicators.append("pain")
    return sorted(set(indicators))


def detect_red_flags(text: str) -> list[str]:
    normalized = normalize_text(text)
    flags = [flag for flag, keywords in RED_FLAG_GROUPS.items() if any(keyword in normalized for keyword in keywords)]
    return sorted(flags)


def conservative_ctas(text: str, emergency_flags: list[str], severity_indicators: list[str], age_group: str) -> int:
    normalized = normalize_text(text)
    if emergency_flags:
        return 1 if any(flag in emergency_flags for flag in {"loss_of_consciousness", "anaphylaxis_signs", "major_trauma"}) else 2
    if any(flag in severity_indicators for flag in {"severe", "worst", "cannot", "unable"}):
        return 3
    if age_group in {"infant", "child"} and ("fever" in normalized or "rash" in normalized):
        return 3
    category = categorize_symptom(text)
    if category in {"respiratory", "neurological", "mental_health"}:
        return 3
    if category in {"gastrointestinal", "musculoskeletal", "dermatology"}:
        return 4
    return 4 if normalized else 5


def recommended_facility_type(ctas_level: int) -> str:
    if ctas_level <= 3:
        return "hospital"
    return "ambulatory" if ctas_level >= 4 else "unknown"


def recommended_urgency_band(ctas_level: int) -> str:
    if ctas_level <= 2:
        return "emergency"
    if ctas_level == 3:
        return "same_day"
    if ctas_level in {4, 5}:
        return "low_acuity"
    return "unknown"


def assess_symptoms(text: str, age_group: str | None = None) -> TriageAssessment:
    chosen_age_group = age_group or "unknown"
    emergency_flags = detect_red_flags(text)
    severity_indicators = detect_severity_indicators(text)
    ctas_level = conservative_ctas(text, emergency_flags, severity_indicators, chosen_age_group)
    emergency_stop = bool(emergency_flags) or ctas_level <= 2
    queue_eligible = not emergency_stop and ctas_level >= 4
    category = categorize_symptom(text)
    summary = (
        "Emergency red flags detected. Route to emergency services immediately."
        if emergency_stop
        else f"Provisional CTAS {ctas_level} estimated conservatively from symptom text and severity markers."
    )
    return TriageAssessment(
        language=detect_language(text),
        patient_age_group=chosen_age_group,
        primary_symptom=extract_primary_symptom(text),
        symptom_category=category,
        duration_hours=parse_duration_to_hours_from_text(text),
        severity_indicators=severity_indicators,
        emergency_flags=emergency_flags,
        emergency_stop=emergency_stop,
        provisional_ctas_level=ctas_level,
        provisional_ctas_label=CTAS_LABELS[ctas_level],
        recommended_facility_type=recommended_facility_type(ctas_level),
        recommended_urgency_band=recommended_urgency_band(ctas_level),
        queue_eligible=queue_eligible,
        reasoning_summary=summary,
    )
