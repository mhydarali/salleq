USE CATALOG montreal_hackathon;
USE SCHEMA salleq_symptom_routing_agent;

INSERT OVERWRITE emergency_keyword_reference
SELECT * FROM VALUES
  ('ek_001', 'chest pain', 'chest pain', 'strong_emergency', true),
  ('ek_002', 'douleur thoracique', 'douleur thoracique', 'strong_emergency', true),
  ('ek_003', 'severe difficulty breathing', 'severe difficulty breathing', 'strong_emergency', true),
  ('ek_004', 'difficulte respiratoire severe', 'difficulte respiratoire severe', 'strong_emergency', true),
  ('ek_005', 'stroke symptoms', 'stroke symptoms', 'strong_emergency', true),
  ('ek_006', 'symptomes d''avc', 'symptomes d''avc', 'strong_emergency', true),
  ('ek_007', 'seizure', 'seizure', 'strong_emergency', true),
  ('ek_008', 'convulsion', 'convulsion', 'strong_emergency', true),
  ('ek_009', 'loss of consciousness', 'loss of consciousness', 'strong_emergency', true),
  ('ek_010', 'perte de conscience', 'perte de conscience', 'strong_emergency', true),
  ('ek_011', 'severe bleeding', 'severe bleeding', 'strong_emergency', true),
  ('ek_012', 'saignement severe', 'saignement severe', 'strong_emergency', true),
  ('ek_013', 'suicidal ideation', 'suicidal ideation', 'strong_emergency', true),
  ('ek_014', 'ideation suicidaire', 'ideation suicidaire', 'strong_emergency', true),
  ('ek_015', 'anaphylaxis', 'anaphylaxis', 'strong_emergency', true),
  ('ek_016', 'anaphylaxie', 'anaphylaxie', 'strong_emergency', true),
  ('ek_017', 'severe allergic reaction', 'severe allergic reaction', 'strong_emergency', true),
  ('ek_018', 'reaction allergique severe', 'reaction allergique severe', 'strong_emergency', true),
  ('ek_019', 'cyanosis', 'cyanosis', 'strong_emergency', true),
  ('ek_020', 'cyanose', 'cyanose', 'strong_emergency', true),
  ('ek_021', 'major trauma', 'major trauma', 'strong_emergency', true),
  ('ek_022', 'traumatisme majeur', 'traumatisme majeur', 'strong_emergency', true),
  ('ek_023', 'unresponsive child', 'unresponsive child', 'strong_emergency', true),
  ('ek_024', 'enfant inconscient', 'enfant inconscient', 'strong_emergency', true),
  ('ek_025', 'high-risk infant symptoms', 'high-risk infant symptoms', 'strong_emergency', true),
  ('ek_026', 'symptomes a haut risque chez le nourrisson', 'symptomes a haut risque chez le nourrisson', 'strong_emergency', true),
  ('ek_027', 'shortness of breath', 'shortness of breath', 'serious_concern', true),
  ('ek_028', 'essoufflement', 'essoufflement', 'serious_concern', true),
  ('ek_029', 'numb face', 'numb face', 'serious_concern', true),
  ('ek_030', 'engourdissement du visage', 'engourdissement du visage', 'serious_concern', true),
  ('ek_031', 'slurred speech', 'slurred speech', 'serious_concern', true),
  ('ek_032', 'difficulte a parler', 'difficulte a parler', 'serious_concern', true),
  ('ek_033', 'lip swelling', 'lip swelling', 'serious_concern', true),
  ('ek_034', 'gonflement des levres', 'gonflement des levres', 'serious_concern', true),
  ('ek_035', 'worsening pain', 'worsening pain', 'mild_concern', true),
  ('ek_036', 'douleur qui empire', 'douleur qui empire', 'mild_concern', true),
  ('ek_037', 'persistent fever', 'persistent fever', 'mild_concern', true),
  ('ek_038', 'fievre persistante', 'fievre persistante', 'mild_concern', true),
  ('ek_039', 'cannot walk', 'cannot walk', 'serious_concern', true),
  ('ek_040', 'incapable de marcher', 'incapable de marcher', 'serious_concern', true)
AS emergency_keyword_reference(keyword_id, phrase, normalized_phrase, severity_class, active_flag);

INSERT OVERWRITE ctas_rules_reference
SELECT * FROM VALUES
  (1, 'Resuscitation', 100, 'emergency_stop', 'Seek immediate medical attention and emergency services now.'),
  (2, 'Emergent', 85, 'emergency_stop', 'Urgent emergency assessment is required now.'),
  (3, 'Urgent', 60, 'hospital_only', 'Hospital emergency assessment is recommended the same day.'),
  (4, 'Less Urgent', 30, 'conditional_queue', 'Hospital or ambulatory assessment may be appropriate depending on stability.'),
  (5, 'Non-Urgent', 10, 'queue_eligible', 'Low-acuity assessment may be appropriate for virtual queue routing.')
AS ctas_rules_reference(ctas_level, ctas_label, base_score, routing_policy, escalation_message);
