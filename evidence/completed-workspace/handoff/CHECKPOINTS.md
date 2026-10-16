# Checkpoints
## Inspection complete � 2026-10-16 � agent-1-inspection
- Real SDK MCP discovery: inspector exposes list_files, read_file, search_files, inspect_dataset, validate_dataset, find_duplicates, write_file.
- inspect_dataset: 8 records, columns question,label; missing question=1, label=0; CSV parses successfully.
- validate_dataset: valid=false, invalid_records=2, invalid_label=1 at record 4, missing_value=1 at record 5; no truncated issues.
- find_duplicates and validation agree: record 3 duplicates record 1; duplicate_records=1, no truncated examples.
- MCP read_file confirms record 4 paymnt, record 6 padded question, record 7 quoted comma, record 8 embedded newline.
- Dataset SHA-256: 9494e4d2774094d4f3480c958a308487ed62e2ba941b5dff1cd9629248febef7
- Rules SHA-256: a58646beb073ac6d0bd3743fa740bcf894106bb5ea21bb91d78065742de76c23
- Policy SHA-256: dca01a45cce70c69cfb602e960d8f41f10c64cb5dada8e46fce8a4655e9c4369
- Inspection report: handoff/INSPECTION_REPORT.md. Raw data, rules and policy unchanged.
- Transcript outside MCP workspace: project-root evidence/agent-1-transcript.jsonl.
## Pending
Fresh-session cleaning; expected 6 retained records; cleaned validation and duplicate checks; original exclusions with reasons; raw preservation hash check; output/report hashes and completion handoff.

## Cleaning and verification complete - 2026-10-16 - agent-2-cleaning
- Fresh real cleaner MCP discovery and file-based continuation completed.
- Rechecked dataset/rules/policy hashes against the saved inspection before mutation; all matched.
- create_clean_copy with all expected hashes atomically created datasets/cleaned/pt1-demo-1/cleaned.csv, excluded.json and report.json.
- Actual counts: 8 input, 6 retained, 2 excluded, 1 trimmed cell, 1 mapped cell.
- Separate validate_dataset: valid=true, records=6, invalid_records=0, duplicate_records=0; no issues or truncated results.
- Separate find_duplicates: 0 duplicate records; inspect_dataset: no missing values.
- Read cleaned CSV: quoted comma and embedded newline preserved. Read exclusions: original records 3 and 5 and reasons preserved.
- Final source SHA-256: 9494e4d2774094d4f3480c958a308487ed62e2ba941b5dff1cd9629248febef7 (unchanged).
- Cleaned SHA-256: c26b3020b271c1587967e24499436990cc076d655f669b95cdb65ad98a6191de
- Excluded SHA-256: 953e0ba616326658e0879a5d3f30b17674e5b45d38f543bf0042cca262812642
- Tool report SHA-256: 70717415dcf0808f275a2288ba8d44dcaced7d5ce76928c51a45a7a3b20cf8ad
- Final report: handoff/CLEANING_REPORT.md, SHA-256 353d3903a0f77742a89175d75ca7002478947510b42d63a92c646fa3a5a85b1c
- Audit transcript: project-root evidence/agent-2-transcript.jsonl outside MCP workspace.
- Four shared handoff records updated with fresh SHA-256 guards. Pending cleaning items above are resolved. No network publication.