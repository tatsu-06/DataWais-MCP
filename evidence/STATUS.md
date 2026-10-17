# Verification status

This file records actual verification, not intended features.

- Implemented: ten-tool MCP file server; three server-enforced roles; resource
  and prompt; protected workspace; deterministic CSV tools; audit and handoff.
- Core test run: 50 passed, including environment-credential handling, symlink protection and rejection of
  agent-writable substitute rule/policy files.
- Live SDK client run: discovery and MCP calls work over localhost.
- Final protocol/security run: 18 checks passed, including strict schemas and
  non-ASCII token rejection after recovery.
- Official MCP Inspector: ten-tool discovery and actual dataset inspection passed.
- Process manager: isolated pm2 automatically recovered the server after a forced
  process stop. The saved handoff survived; evidence is process-recovery.json.
- HTTPS: DEPLOYED after user authorization. Cloudflare tunnel and server are
  supervised by pm2. The wrapper automatically synchronizes a changed hostname.
- Public endpoint: https://separated-northeast-lanka-acids.trycloudflare.com/mcp
- Public protocol/security run: 18 checks passed through normal DNS with no IP
  override. The earlier router NXDOMAIN cache has resolved without changing
  network settings. See public-http-checks.json.
- Codex: DataWais connection added with a private authentication helper and
  cleaner-role access. Existing connections preserved. A fresh chat/reload is
  was used to discover newly registered tools. Native Codex tool calls are now
  verified in this chat; see native-codex-audit.json.
- Startup: a current-user, limited-privilege sign-in task starts the server and
  tunnel. Start/stop/disable-autostart controls are included.
- Multi-agent demonstration: COMPLETE through two fresh AI agent contexts.
  Inspector used 20 tool calls, with no tool errors. Cleaner used 28 calls, with
  one handled missing-directory error before creating the first output run.
  The initializer now creates empty output directories for future runs. Neither
  transcript was edited to hide errors.
- Actual result: 8 input records -> 6 retained, 2 exclusions, 1 whitespace
  correction and 1 explicit label mapping. Independent validation passes with
  zero duplicates. Raw data SHA-256 is unchanged.
- Read DEMONSTRATION.md, the full JSONL transcripts and completed-workspace/ for
  the reproducible evidence. HTTP checks are clearly labeled as scripted tests.
- Hosted repository: https://github.com/tatsu-06/DataWais-MCP (public after explicit
  user approval). Anonymous access to the repository and PDF report is verified.
- A seven-page upload report is included at docs/DataWais-PT1-Submission.pdf.
  The team still needs to perform its assessed five-minute presentation.
