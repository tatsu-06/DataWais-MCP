# DataWais is set up

The server and authenticated HTTPS tunnel are running on the original computer.
They start automatically when you sign in. Existing Codex tools were preserved.

## Use it in Codex

Open a fresh Codex chat so it loads the new **datawais** MCP connection. If the
connection is not visible, close and reopen Codex once. Then ask:

> Use DataWais MCP. Read the shared project state, show the dataset quality
> results, and explain how the two agent sessions completed the cleaning task.

Codex uses the stable local endpoint and the cleaner role. Its private
authentication helper reads credentials locally; you do not need to paste a
token. The cleaner has nine tools and cannot delete files.

## Simple controls

- **START-DATAWAIS.cmd:** start/check the server and HTTPS tunnel.
- **STOP-DATAWAIS.cmd:** stop both services.
- **DISABLE-AUTOSTART.cmd:** disable sign-in startup.

Keep this computer awake and connected for the remote endpoint to work. These
controls and the scheduled task refer to this original project location.

## What to submit or present

- `DataWais-MCP.zip`: source, documentation, Git history and demonstration evidence.
- `evidence/DEMONSTRATION.md`: readable index of the actual two-session run.
- `evidence/agent-1-transcript.jsonl` and `agent-2-transcript.jsonl`: full calls.
- `evidence/completed-workspace/`: verified handoff, datasets and outputs.
- `docs/REPORT.md`: implementation choices and security tradeoffs.
- `docs/DEMO.md`: five-minute presentation guide.

The recorded result is 8 input records, 6 retained, 2 exclusions and an unchanged
original file. The final automated suite has 50 passing tests. Live MCP checks
passed locally and through HTTPS.

## Remote connection

The current address is recorded in `.runtime/public-url.txt`. Ready-to-use
authenticated connection entries are in `.runtime/public-clients.json`. Those
private files stay out of the shared archive.

A quick-tunnel address can change after a restart. The tunnel wrapper updates
the exact allowed hostname and private connection files automatically. For a
fixed semester-long URL, an operator-owned named tunnel/domain would be needed.

The initial Wi-Fi router DNS-cache issue has resolved. All 18 public
protocol/security checks now pass through normal DNS with no override. Codex's
local connection and native tools are also verified. No network settings were
changed. See `evidence/public-http-checks.json` for the latest result.

The repository is local; it has not been uploaded to a Git hosting account.
The source ZIP includes `repository-history.bundle` to preserve its Git history.
See `docs/PT1-CHECKLIST.md` for the requirement audit: the hosted repository link
and the team's assessed live presentation remain.
