# PT1 requirements audit

Checked against the supplied presentation's project brief and rubric (printed
slides 16–20; PDF pages 12–16). This is an evidence audit, not a predicted grade.

## Minimum technical requirements

| Requirement | Status | Evidence |
|---|---|---|
| Sandboxed workspace; reject paths escaping it | Complete | core.py and tests/test_core.py; live traversal rejection |
| At least 8 tools, including list/read/write/str_replace/delete plus search or git-lite | Complete | Admin exposes all 10; inspector has 7 and cleaner 9 by design; tool discovery and real calls |
| HTTPS tunnel plus process manager | Complete | Cloudflare tunnel and server online under pm2; public-http-checks.json |
| PROJECT_STATE, PLAN_LOG, CHECKPOINTS, DECISIONS | Complete | fixtures/handoff, live workspace and recorded handoff snapshots |
| Real MCP client; one multi-step task across 2+ agent sessions | Complete | Two fresh AI agent contexts; full transcripts; official Inspector; native Codex connection |
| Short report covering stack, tools and security tradeoffs | Complete | docs/REPORT.md |

The sample task inspected, validated and cleaned a real CSV file through MCP:
8 source records, 6 retained, 2 exclusions, no remaining invalid records or
duplicates. The original source hash remains unchanged. The records themselves
are synthetic demonstration data.

## Submission deliverables

| Deliverable | Status |
|---|---|
| Working repository | Complete locally, with Git history and a portable bundle |
| Repository link | **Not complete: no Git remote or hosted repository URL is configured** |
| README | Written, with installation, tools, deployment and security guidance |
| Tool-call transcript | Complete: agent-1-transcript.jsonl and agent-2-transcript.jsonl |
| Short report | Complete: docs/REPORT.md |
| PLAN_LOG and checkpoint files | Complete and included in evidence |
| Five-minute live demonstration | **Not complete as an assessed presentation: a run and guide exist; the team must rehearse and present it** |

## Rubric review

- **Agent efficiency, 20 points:** The task finished and the calls are recorded.
  Inspection took 20 tool calls; continuation took 28, including one handled
  missing-directory error. Full marks are not guaranteed: the live workflow can
  be tightened, with independent reads batched where the host supports it.
- **Agent/tool management, 20 points:** Separate roles, server-enforced tool
  scope, guarded destructive operations, explicit handoff and audit logs exist.
- **Tool design, 20 points:** Ten single-purpose tools have strict schemas,
  descriptions and helpful error results. Inspector and real-client evidence exist.
- **Architecture, 15 points:** Choices are explained in the report. Managed
  server credentials are supplied through environment variables; local bootstrap
  and client credentials remain in ignored private runtime files. Restart
  recovery has been demonstrated.
- **Security, 10 points:** Path protection, authenticated public access, guarded
  deletion, immutable source data and documented limits are implemented.
- **Documentation/demo, 15 points:** Documentation and meaningful Git commits
  exist. A fresh-machine/classmate reproduction and a timed presentation have
  not been independently verified.

## Latest verification

- 50 automated tests passed.
- 18 public MCP protocol/security checks passed through normal DNS, without an
  IP override. The earlier router DNS-cache issue has resolved.
- Native Codex tools successfully read current state, validate the cleaned copy,
  inspect the unchanged original, search files and update stale deployment state.
- The server and tunnel remain managed by pm2; sign-in startup is configured.

## Remaining actions

1. Publish the local repository to the chosen Git hosting account and submit its
   link with the README, transcripts, report and handoff evidence.
2. Rehearse the actual workflow within five minutes and present it at the
   instructor's checkpoint. Be ready to explain MCP, roles, sandboxing and tradeoffs.
3. Before presenting, check the current tunnel URL and keep the computer awake
   and online. A quick-tunnel URL can change on restart; the wrapper updates the
   private connection files automatically.

Optional strengthening: ask a classmate to reproduce the README setup and use
the rehearsal to remove redundant tool calls. No score is claimed in advance.
