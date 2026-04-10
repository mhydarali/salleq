# SalleQ Symptom Routing Agent

## Purpose

This project implements a Databricks-native symptom-routing agent for a Quebec virtual non-emergency waiting room workflow. The system is not a chatbot and must never act like one. Its only job is to convert symptom text into a strict routing JSON payload for a frontend application.

## Architecture

1. Unity Catalog stores editable reference data in:
   - `emergency_keyword_reference`
   - `ctas_rules_reference`
   - `intake_sessions_simulated`
2. Deterministic Python scoring logic lives in:
   - `src/scoring/emergency_logic.py`
   - `src/scoring/ctas_logic.py`
   - `src/scoring/risk_score.py`
3. Request parsing and JSON assembly live in:
   - `src/utils/parsing.py`
   - `src/assistant/tools.py`
4. The Databricks agent entry point lives in:
   - `src/assistant/agent.py`
5. SQL, notebooks, and tests validate the safety gates and output contract.

## Safety Constraints

- Never diagnose.
- Never provide treatment advice.
- Never present the output as a substitute for nurse triage.
- Use the exact product positioning:
  - `AI-estimated provisional CTAS urgency for routing support only. Final triage is determined by clinical staff.`
- Be conservative.
- If uncertain, choose the higher-acuity CTAS level.
- Any emergency red flag, CTAS 1, CTAS 2, or critical risk band must stop the flow.
- Emergency stop always means:
  - `queue_eligible = false`
  - `recommended_facility_type = hospital`
  - `recommended_urgency_band = emergency`
- JSON-only output is mandatory for any agent invocation.

## Output Contract

The agent must return this exact JSON shape and must not add or remove keys without approval:

- `language`
- `patient_age_group`
- `primary_symptom`
- `symptom_category`
- `duration_hours`
- `severity_indicators`
- `emergency_flags`
- `emergency_stop`
- `provisional_ctas_level`
- `provisional_ctas_label`
- `recommended_facility_type`
- `recommended_urgency_band`
- `queue_eligible`
- `risk_score`
- `risk_band`
- `reasoning_summary`

See `src/assistant/output_schema.json` for the machine-readable schema.

## Implementation Order

1. Scaffold the workspace project.
2. Create and maintain the files under `skills/`.
3. Create the Unity Catalog schema and reference tables.
4. Seed reference data and simulated cases.
5. Implement deterministic emergency, CTAS, and risk-scoring logic.
6. Wrap the logic in a `ResponsesAgent`.
7. Add notebooks and tests.
8. Update the README and demo instructions.

## How To Use The Skills Folder

The files under `skills/` are execution checklists for a coding assistant. Run them in numerical order. Each file defines:

- goal
- files to create or modify
- acceptance criteria
- validation steps

Do not skip a lower-numbered skill when making material changes.

## Never Change Without Approval

- Output JSON keys or enum values
- Safety-stop rules
- CTAS labels
- Risk score formula weights
- Risk band thresholds
- Emergency keyword semantics
- The required disclaimer text
- The rule that the system is not a diagnostic or treatment tool
