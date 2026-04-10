from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.symptom_routing.assistant.tools import build_routing_decision


CATALOG = "montreal_hackathon"
SCHEMA = "salleq_symptom_routing_agent"
TABLE = "intake_sessions_simulated"


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    texts: dict[str, str]
    age_groups: tuple[str, ...]
    baseline_duration_hours: int
    worsening_duration_hours: int


GENERAL_SCENARIOS = (
    Scenario("general_001", {"en": "Fever and ear pain since this morning", "fr": "Fievre et douleur a l oreille depuis ce matin"}, ("adult", "child", "older_adult"), 8, 30),
    Scenario("general_002", {"en": "Twisted ankle with swelling after a fall", "fr": "Cheville tordue avec gonflement apres une chute"}, ("adult", "child", "older_adult"), 4, 28),
    Scenario("general_003", {"en": "Sore throat and fever for one day", "fr": "Mal de gorge et fievre depuis un jour"}, ("adult", "child", "older_adult"), 16, 48),
    Scenario("general_004", {"en": "Minor cut on hand with light bleeding", "fr": "Petite coupure a la main avec saignement leger"}, ("adult", "child", "older_adult"), 2, 20),
    Scenario("general_005", {"en": "Abdominal pain with nausea since yesterday", "fr": "Douleur abdominale avec nausee depuis hier"}, ("adult", "child", "older_adult"), 20, 40),
    Scenario("general_006", {"en": "Headache with nausea and light sensitivity", "fr": "Mal de tete avec nausee et sensibilite a la lumiere"}, ("adult", "child", "older_adult"), 10, 36),
    Scenario("general_007", {"en": "Chest pain and pressure for two hours", "fr": "Douleur thoracique et pression depuis deux heures"}, ("adult", "older_adult", "child"), 2, 6),
    Scenario("general_008", {"en": "Shortness of breath and cough", "fr": "Essoufflement et toux"}, ("adult", "older_adult", "child"), 6, 24),
    Scenario("general_009", {"en": "Rash and itching after a new food", "fr": "Eruption et demangeaisons apres un nouvel aliment"}, ("adult", "child", "older_adult"), 3, 18),
    Scenario("general_010", {"en": "Vomiting and diarrhea since last night", "fr": "Vomissements et diarrhee depuis la nuit derniere"}, ("adult", "child", "older_adult"), 12, 30),
    Scenario("general_011", {"en": "Back pain after lifting boxes", "fr": "Douleur au dos apres avoir souleve des boites"}, ("adult", "older_adult", "child"), 6, 72),
    Scenario("general_012", {"en": "Burning urination and low fever", "fr": "Brulure urinaire et legere fievre"}, ("adult", "older_adult", "child"), 14, 40),
    Scenario("general_013", {"en": "Migraine worse today with vomiting", "fr": "Migraine pire aujourd hui avec vomissements"}, ("adult", "older_adult", "child"), 8, 26),
    Scenario("general_014", {"en": "Severe bleeding from a deep leg cut", "fr": "Saignement severe d une coupure profonde a la jambe"}, ("adult", "older_adult", "child"), 1, 2),
    Scenario("general_015", {"en": "Facial numbness and slurred speech", "fr": "Engourdissement du visage et difficulte a parler"}, ("adult", "older_adult", "child"), 1, 3),
    Scenario("general_016", {"en": "Painful swollen knee after twisting", "fr": "Genou douloureux et gonfle apres une torsion"}, ("adult", "older_adult", "child"), 5, 36),
    Scenario("general_017", {"en": "Loss of consciousness with blue lips", "fr": "Perte de conscience avec levres bleues"}, ("adult", "older_adult", "child"), 1, 2),
)

CHILD_SCENARIOS = (
    Scenario("child_001", {"en": "Child wheezing and breathing fast", "fr": "Enfant qui siffle en respirant et respire vite"}, ("child",), 2, 8),
    Scenario("child_002", {"en": "Child fell at school and has wrist pain", "fr": "Enfant tombe a l ecole avec douleur au poignet"}, ("child",), 3, 18),
    Scenario("child_003", {"en": "Child has hives and lip swelling", "fr": "Enfant avec urticaire et gonflement des levres"}, ("child",), 1, 3),
    Scenario("child_004", {"en": "Child with fever, sore throat, and worsening pain", "fr": "Enfant avec fievre, mal de gorge et douleur qui empire"}, ("child",), 10, 32),
)

INFANT_SCENARIOS = (
    Scenario("infant_001", {"en": "Infant fever with poor feeding", "fr": "Nourrisson avec fievre et alimentation reduite"}, ("infant",), 4, 12),
    Scenario("infant_002", {"en": "Infant hard to wake and breathing poorly", "fr": "Nourrisson difficile a reveiller et respire mal"}, ("infant",), 1, 2),
    Scenario("infant_003", {"en": "Infant vomiting and fewer wet diapers", "fr": "Nourrisson qui vomit et moins de couches mouillees"}, ("infant",), 6, 24),
    Scenario("infant_004", {"en": "Infant cough with fever and wheezing", "fr": "Nourrisson avec toux, fievre et sifflement respiratoire"}, ("infant",), 8, 20),
    Scenario("infant_005", {"en": "Infant unresponsive with blue lips", "fr": "Nourrisson inconscient avec levres bleues"}, ("infant",), 1, 2),
)

ALL_SCENARIOS = GENERAL_SCENARIOS + CHILD_SCENARIOS + INFANT_SCENARIOS


def _build_case_text(scenario: Scenario, language: str, worsening: bool) -> str:
    suffix = {
        "en": " It is getting worse today." if worsening else " The patient is stable for now.",
        "fr": " La situation empire aujourd hui." if worsening else " La situation semble stable pour le moment.",
    }
    return scenario.texts[language] + suffix[language]


def generate_simulated_cases() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    counter = 1
    for scenario in ALL_SCENARIOS:
        for age_group in scenario.age_groups:
            for language in ("en", "fr"):
                for worsening in (False, True):
                    raw_symptom_text = _build_case_text(scenario, language, worsening)
                    duration_hours = scenario.worsening_duration_hours if worsening else scenario.baseline_duration_hours
                    payload = build_routing_decision(
                        symptom_text=raw_symptom_text,
                        patient_age_group=age_group,
                        explicit_duration_hours=duration_hours,
                    )
                    rows.append(
                        {
                            "intake_session_id": f"sim-{counter:04d}",
                            "created_at": "2026-03-27T12:00:00Z",
                            "raw_symptom_text": raw_symptom_text,
                            **payload,
                        }
                    )
                    counter += 1
    return rows


def _sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "array(" + ", ".join(_sql_literal(item) for item in value) + ")"
    text = str(value).replace("'", "''")
    return f"'{text}'"


def build_seed_sql(full_table_name: str | None = None) -> str:
    rows = generate_simulated_cases()
    target_table = full_table_name or f"{CATALOG}.{SCHEMA}.{TABLE}"
    header = [
        "USE CATALOG montreal_hackathon;",
        "USE SCHEMA salleq_symptom_routing_agent;",
        f"INSERT OVERWRITE {target_table}",
        "SELECT * FROM VALUES",
    ]
    value_lines = []
    for row in rows:
        value_lines.append(
            "("
            + ", ".join(
                [
                    _sql_literal(row["intake_session_id"]),
                    f"to_timestamp({_sql_literal(row['created_at'])})",
                    _sql_literal(row["language"]),
                    _sql_literal(row["patient_age_group"]),
                    _sql_literal(row["raw_symptom_text"]),
                    _sql_literal(row["primary_symptom"]),
                    _sql_literal(row["symptom_category"]),
                    _sql_literal(row["duration_hours"]),
                    _sql_literal(row["severity_indicators"]),
                    _sql_literal(row["emergency_flags"]),
                    _sql_literal(row["emergency_stop"]),
                    _sql_literal(row["provisional_ctas_level"]),
                    _sql_literal(row["provisional_ctas_label"]),
                    _sql_literal(row["recommended_facility_type"]),
                    _sql_literal(row["recommended_urgency_band"]),
                    _sql_literal(row["queue_eligible"]),
                    _sql_literal(row["risk_score"]),
                    _sql_literal(row["risk_band"]),
                    _sql_literal(row["reasoning_summary"]),
                ]
            )
            + ")"
        )
    sql = "\n".join(header)
    sql += "\n" + ",\n".join(value_lines)
    sql += "\nAS intake_sessions_simulated("
    sql += ", ".join(
        [
            "intake_session_id",
            "created_at",
            "language",
            "patient_age_group",
            "raw_symptom_text",
            "primary_symptom",
            "symptom_category",
            "duration_hours",
            "severity_indicators",
            "emergency_flags",
            "emergency_stop",
            "provisional_ctas_level",
            "provisional_ctas_label",
            "recommended_facility_type",
            "recommended_urgency_band",
            "queue_eligible",
            "risk_score",
            "risk_band",
            "reasoning_summary",
        ]
    )
    sql += ");\n"
    return sql


def write_seed_sql(output_path: Path | None = None) -> Path:
    target_path = output_path or PROJECT_ROOT / "sql" / "symptom_routing" / "03_seed_simulated_cases.sql"
    target_path.write_text(build_seed_sql())
    return target_path


if __name__ == "__main__":
    path = write_seed_sql()
    print(f"Wrote simulated seed SQL to {path}")
    print(f"Generated {len(generate_simulated_cases())} simulated cases")
