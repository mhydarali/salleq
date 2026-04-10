USE CATALOG montreal_hackathon;

CREATE SCHEMA IF NOT EXISTS salleq_ctas_virtual_waiting_room
COMMENT 'SalleQ Quebec-first virtual waiting room application data';

USE SCHEMA salleq_ctas_virtual_waiting_room;

CREATE VOLUME IF NOT EXISTS raw_landing
COMMENT 'Raw landing zone for facility master and Quebec ER scrape artifacts';

CREATE TABLE IF NOT EXISTS facility_master (
  `index` STRING,
  facility_name STRING,
  source_facility_type STRING,
  odhf_facility_type STRING,
  provider STRING,
  unit STRING,
  street_no STRING,
  street_name STRING,
  postal_code STRING,
  city STRING,
  province STRING,
  source_format_str_address STRING,
  csdname STRING,
  csduid DOUBLE,
  pruid INT,
  latitude DOUBLE,
  longitude DOUBLE,
  full_address STRING,
  facility_id_normalized STRING,
  is_quebec BOOLEAN,
  ingested_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qc_er_live_status_bronze (
  scrape_id STRING,
  source_url STRING,
  raw_html_fragment STRING,
  facility_name_raw STRING,
  address_raw STRING,
  region_raw STRING,
  metric_payload STRING,
  scraped_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qc_er_live_status_silver (
  scrape_id STRING,
  facility_name_raw STRING,
  address_raw STRING,
  region STRING,
  wait_time_non_priority_minutes INT,
  people_waiting INT,
  total_people_er INT,
  stretcher_occupancy_pct DOUBLE,
  avg_wait_room_minutes_prev_day INT,
  avg_stretcher_wait_minutes_prev_day INT,
  source_url STRING,
  scraped_at TIMESTAMP,
  normalized_facility_name STRING,
  normalized_address STRING
);

CREATE TABLE IF NOT EXISTS qc_er_live_status (
  scrape_id STRING,
  facility_name_raw STRING,
  address_raw STRING,
  region STRING,
  wait_time_non_priority_minutes INT,
  people_waiting INT,
  total_people_er INT,
  stretcher_occupancy_pct DOUBLE,
  avg_wait_room_minutes_prev_day INT,
  avg_stretcher_wait_minutes_prev_day INT,
  source_url STRING,
  scraped_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qc_facility_match (
  facility_name_raw STRING,
  address_raw STRING,
  matched_facility_id STRING,
  matched_facility_name STRING,
  match_confidence DOUBLE,
  match_method STRING,
  manually_validated BOOLEAN,
  matched_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manual_facility_overrides (
  facility_name_raw STRING,
  address_raw STRING,
  matched_facility_id STRING,
  matched_facility_name STRING,
  reason STRING,
  updated_by STRING,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intake_sessions (
  intake_session_id STRING,
  created_at TIMESTAMP,
  language STRING,
  patient_age_group STRING,
  primary_symptom STRING,
  symptom_category STRING,
  duration_hours DOUBLE,
  severity_indicators ARRAY<STRING>,
  emergency_flags ARRAY<STRING>,
  emergency_stop BOOLEAN,
  provisional_ctas_level INT,
  provisional_ctas_label STRING,
  recommended_facility_type STRING,
  recommended_urgency_band STRING,
  queue_eligible BOOLEAN,
  reasoning_summary STRING
);

CREATE TABLE IF NOT EXISTS virtual_queue (
  queue_id STRING,
  intake_session_id STRING,
  facility_id STRING,
  arrival_window_start TIMESTAMP,
  arrival_window_end TIMESTAMP,
  queue_position INT,
  estimated_call_time TIMESTAMP,
  notification_preference STRING,
  queue_status STRING,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contact_info (
  contact_id STRING,
  queue_id STRING,
  channel_type STRING,
  encrypted_contact_value STRING,
  expires_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ctas_rules_reference (
  ctas_level INT,
  ctas_label STRING,
  routing_policy STRING,
  escalation_message STRING,
  queue_eligible BOOLEAN,
  facility_type_guidance STRING
);

CREATE TABLE IF NOT EXISTS emergency_keyword_reference (
  keyword STRING,
  language STRING,
  flag_label STRING,
  severity_weight INT,
  note STRING
);

CREATE TABLE IF NOT EXISTS staff_facility_scope (
  user_name STRING,
  facility_id_normalized STRING,
  role_name STRING,
  region_scope STRING,
  created_at TIMESTAMP
);

INSERT OVERWRITE ctas_rules_reference VALUES
  (1, 'Resuscitation', 'Hard stop. Direct user to immediate emergency services and do not permit queue enrollment.', 'Call emergency services or go to the nearest emergency department immediately.', false, 'hospital'),
  (2, 'Emergent', 'Hard stop. Direct user to emergency services and do not permit queue enrollment.', 'Immediate emergency assessment is required. Do not use the virtual queue.', false, 'hospital'),
  (3, 'Urgent', 'Allow hospital routing only. Do not offer ambulatory recommendations or virtual non-emergency queue.', 'Urgent hospital assessment is recommended as soon as possible.', false, 'hospital'),
  (4, 'Less Urgent', 'Allow hospital and ambulatory routing when clinically appropriate. Virtual queue allowed.', 'Non-emergency routing support only. Final triage remains clinical.', true, 'hospital_or_ambulatory'),
  (5, 'Non-Urgent', 'Prefer ambulatory or primary-care style routing while still keeping hospital options visible.', 'Non-emergency routing support only. Final triage remains clinical.', true, 'ambulatory_preferred');

INSERT OVERWRITE emergency_keyword_reference VALUES
  ('chest pain', 'en', 'chest_pain', 10, 'Potential cardiac emergency'),
  ('douleur thoracique', 'fr', 'chest_pain', 10, 'Douleur thoracique'),
  ('shortness of breath', 'en', 'severe_difficulty_breathing', 10, 'Respiratory distress'),
  ('difficulty breathing', 'en', 'severe_difficulty_breathing', 10, 'Respiratory distress'),
  ('difficulte respiratoire', 'fr', 'severe_difficulty_breathing', 10, 'Detresse respiratoire'),
  ('stroke', 'en', 'stroke_symptoms', 10, 'Possible stroke'),
  ('avc', 'fr', 'stroke_symptoms', 10, 'Possible AVC'),
  ('seizure', 'en', 'seizure', 10, 'Neurological emergency'),
  ('convulsion', 'fr', 'seizure', 10, 'Urgence neurologique'),
  ('loss of consciousness', 'en', 'loss_of_consciousness', 10, 'Loss of consciousness'),
  ('unconscious', 'en', 'loss_of_consciousness', 10, 'Loss of consciousness'),
  ('perte de conscience', 'fr', 'loss_of_consciousness', 10, 'Perte de conscience'),
  ('severe bleeding', 'en', 'severe_bleeding', 10, 'Hemorrhage risk'),
  ('hemorrhage', 'en', 'severe_bleeding', 10, 'Hemorrhage risk'),
  ('saignement important', 'fr', 'severe_bleeding', 10, 'Hemorragie'),
  ('suicidal', 'en', 'suicidal_ideation', 10, 'Psychiatric emergency'),
  ('suicidaire', 'fr', 'suicidal_ideation', 10, 'Urgence psychiatrique'),
  ('anaphylaxis', 'en', 'anaphylaxis_signs', 10, 'Severe allergy emergency'),
  ('anaphylaxie', 'fr', 'anaphylaxis_signs', 10, 'Urgence allergique grave'),
  ('allergic reaction', 'en', 'severe_allergic_reaction', 9, 'Severe allergy'),
  ('reaction allergique', 'fr', 'severe_allergic_reaction', 9, 'Reaction allergique grave'),
  ('cyanosis', 'en', 'cyanosis', 10, 'Hypoxia sign'),
  ('cyanose', 'fr', 'cyanosis', 10, 'Signe d hypoxie'),
  ('major trauma', 'en', 'major_trauma', 10, 'Major trauma'),
  ('traumatisme majeur', 'fr', 'major_trauma', 10, 'Traumatisme majeur'),
  ('unresponsive child', 'en', 'unresponsive_child', 10, 'Pediatric emergency'),
  ('child not responding', 'en', 'unresponsive_child', 10, 'Pediatric emergency'),
  ('enfant inconscient', 'fr', 'unresponsive_child', 10, 'Urgence pediatrique'),
  ('infant fever', 'en', 'high_risk_infant_symptoms', 9, 'High-risk infant symptom'),
  ('nourrisson', 'fr', 'high_risk_infant_symptoms', 9, 'Symptome nourrisson a risque');
