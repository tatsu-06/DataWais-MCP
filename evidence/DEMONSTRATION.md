# Actual two-session MCP demonstration

Two fresh AI agent contexts selected the following real MCP calls through the
official Python SDK client. This is distinct from scripts/check_http.py.

The second agent was not given the first conversation or its findings. Its
task instructions directed it to discover and continue from shared handoff.

## agent-1-inspection (inspector)

20 tool calls; 0 tool errors.

| # | Operation | Tool | Result |
|---|---|---|---|
| 1 | list | discovery | success |
| 2 | call | read_file | success |
| 3 | call | read_file | success |
| 4 | call | read_file | success |
| 5 | call | inspect_dataset | success |
| 6 | call | find_duplicates | success |
| 7 | call | read_file | success |
| 8 | call | read_file | success |
| 9 | call | validate_dataset | success |
| 10 | call | read_file | success |
| 11 | call | read_file | success |
| 12 | call | list_files | success |
| 13 | call | list_files | success |
| 14 | call | write_file | success |
| 15 | call | write_file | success |
| 16 | call | write_file | success |
| 17 | call | write_file | success |
| 18 | call | write_file | success |
| 19 | call | write_file | success |
| 20 | call | read_file | success |
| 21 | call | inspect_dataset | success |

## agent-2-cleaning (cleaner)

28 tool calls; 1 tool errors.

| # | Operation | Tool | Result |
|---|---|---|---|
| 1 | list | discovery | success |
| 2 | call | read_file | success |
| 3 | call | list_files | success |
| 4 | call | read_file | success |
| 5 | call | read_file | success |
| 6 | call | read_file | success |
| 7 | call | read_file | success |
| 8 | call | read_file | success |
| 9 | call | read_file | success |
| 10 | call | inspect_dataset | success |
| 11 | call | list_files | error |
| 12 | call | list_files | success |
| 13 | call | create_clean_copy | success |
| 14 | call | validate_dataset | success |
| 15 | call | find_duplicates | success |
| 16 | call | inspect_dataset | success |
| 17 | call | read_file | success |
| 18 | call | read_file | success |
| 19 | call | read_file | success |
| 20 | call | inspect_dataset | success |
| 21 | call | write_file | success |
| 22 | call | read_file | success |
| 23 | call | write_file | success |
| 24 | call | read_file | success |
| 25 | call | write_file | success |
| 26 | call | read_file | success |
| 27 | call | write_file | success |
| 28 | call | read_file | success |
| 29 | call | write_file | success |

## Read the evidence

- agent-1-transcript.jsonl and agent-2-transcript.jsonl: complete inputs/results.
- agent-1-handoff/: the first agent's saved continuation instructions.
- completed-workspace/: the verified final files, rules and dataset outputs.
- server-audit.jsonl: server-side request/handler records, without credentials.
- inspector-tools.json and inspector-inspection.json: official Inspector results.
- http-checks.json: scripted protocol/security verification, not an agent run.

All dataset records in this package are synthetic demonstration data.
