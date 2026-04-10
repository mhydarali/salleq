# Goal

Create the Unity Catalog schema, reference tables, SQL helper functions, and reference seed data.

# Files To Create Or Modify

- `sql/01_schema.sql`
- `sql/02_reference_data.sql`
- `sql/03_seed_simulated_cases.sql`

# Acceptance Criteria

- The schema creates:
  - `emergency_keyword_reference`
  - `ctas_rules_reference`
  - `intake_sessions_simulated`
- SQL helper functions for CTAS labels and risk bands exist.
- Reference data includes English and French emergency phrases.
- Simulated seed SQL is available for at least 200 cases.

# Validation Steps

1. Execute `sql/01_schema.sql` successfully.
2. Execute `sql/02_reference_data.sql` successfully.
3. Query reference table row counts.
4. Seed `intake_sessions_simulated` and confirm at least 200 rows.
