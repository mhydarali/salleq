CREATE SCHEMA IF NOT EXISTS montreal_hackathon.salleq_symptom_routing_agent
COMMENT 'SalleQ symptom routing agent reference data, simulated intakes, and helper functions';

USE CATALOG montreal_hackathon;
USE SCHEMA salleq_symptom_routing_agent;

CREATE OR REPLACE TABLE emergency_keyword_reference (
  keyword_id STRING NOT NULL,
  phrase STRING NOT NULL,
  normalized_phrase STRING NOT NULL,
  severity_class STRING NOT NULL,
  active_flag BOOLEAN NOT NULL
)
COMMENT 'Editable emergency red-flag phrases used for validation and governance';

CREATE OR REPLACE TABLE ctas_rules_reference (
  ctas_level INT NOT NULL,
  ctas_label STRING NOT NULL,
  base_score INT NOT NULL,
  routing_policy STRING NOT NULL,
  escalation_message STRING NOT NULL
)
COMMENT 'Governed CTAS routing reference used by the symptom-routing agent';

CREATE OR REPLACE TABLE intake_sessions_simulated (
  intake_session_id STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  language STRING NOT NULL,
  patient_age_group STRING NOT NULL,
  raw_symptom_text STRING NOT NULL,
  primary_symptom STRING NOT NULL,
  symptom_category STRING NOT NULL,
  duration_hours INT NOT NULL,
  severity_indicators ARRAY<STRING> NOT NULL,
  emergency_flags ARRAY<STRING> NOT NULL,
  emergency_stop BOOLEAN NOT NULL,
  provisional_ctas_level INT NOT NULL,
  provisional_ctas_label STRING NOT NULL,
  recommended_facility_type STRING NOT NULL,
  recommended_urgency_band STRING NOT NULL,
  queue_eligible BOOLEAN NOT NULL,
  risk_score INT NOT NULL,
  risk_band STRING NOT NULL,
  reasoning_summary STRING NOT NULL
)
COMMENT 'Deterministically generated simulated symptom intake cases for demo and validation';

CREATE OR REPLACE FUNCTION ctas_label_from_level(ctas_level INT)
RETURNS STRING
RETURN CASE ctas_level
  WHEN 1 THEN 'Resuscitation'
  WHEN 2 THEN 'Emergent'
  WHEN 3 THEN 'Urgent'
  WHEN 4 THEN 'Less Urgent'
  WHEN 5 THEN 'Non-Urgent'
  ELSE 'Non-Urgent'
END;

CREATE OR REPLACE FUNCTION risk_band_from_score(risk_score INT)
RETURNS STRING
RETURN CASE
  WHEN risk_score >= 75 THEN 'critical'
  WHEN risk_score >= 50 THEN 'high'
  WHEN risk_score >= 25 THEN 'moderate'
  ELSE 'low'
END;
