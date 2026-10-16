# Checkpoints
## Inspection complete — 2026-10-16 — agent-1-inspection
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
