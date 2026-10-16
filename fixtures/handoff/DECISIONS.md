# Decisions
The operator supplied rules/cleaning_policy.json before agent access.
Only its explicit label mapping may be applied. Never infer corrections.
Preserve raw data. Keep rejected original records and reasons in excluded.json.
Exact duplicate detection occurs after configured trimming and label mapping.
Validate required fields and labels before selecting duplicate survivors.
