# DataWais MCP

**A working MCP file-server connector with CSV quality tools and persistent AI handoff.**

DataWais exposes a sandboxed project folder through MCP Streamable HTTP. AI agents
can inspect CSV data, validate declared rules, identify duplicates, and create
cleaned copies. The original data and operator-supplied rules are read-only to
every agent role. No model API is called inside the server.

## What's included

- Ten working tools, strict input schemas, structured results and `isError` errors.
- Three token-scoped roles: inspector (7 tools), cleaner (9), admin (10).
- A project-state resource and a reusable continuation prompt.
- A real MCP SDK client, live protocol checks and security/CSV tests.
- pm2 supervision, HTTPS tunnel configuration, example data and handoff templates.
- Demo prompts, technical report and evidence from the actual runs.

## Install on Windows

Install Python 3.11+ (3.12 recommended), Node.js and Git first. In this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
.\.venv\Scripts\python.exe scripts\init_demo.py
.\.venv\Scripts\python.exe -m datawais.server
```

The server binds to `127.0.0.1:8765`; MCP is at `/mcp`. A token is required.
The initializer generates three random tokens in `.runtime/secrets.json`. Never
commit that file. The initializer refuses to overwrite an existing workspace.
Use a different `--root` for another untouched fixture set.

The build in this chat used the bundled Python 3.12 runtime and dependencies in
the chat's `work/` folder because environment restrictions prevented normal venv
bootstrapping. `scripts/bootstrap.py` supports this using `DATAWAIS_DEPS`. Normal
installations can run the package directly without that variable.

On the original computer, `scripts/Run-Here.ps1` restarts the already configured
local installation. Private runtime settings stay outside the source archive.
For exact tested dependency versions, install `requirements-lock.txt` before
installing this package with `--no-deps`.

## Test the running connector

From a second terminal:

```powershell
.\.venv\Scripts\python.exe -m datawais.client --role admin list
.\.venv\Scripts\python.exe scripts\check_http.py
.\.venv\Scripts\python.exe -m pytest -q
```

The client performs MCP initialization and real `tools/list` / `tools/call`
exchanges. It is a connector for the agent operating it, not an LLM agent itself.

To call a tool, create `inspect-args.json` containing:

```json
{"path":"datasets/raw/university_questions.csv","sample_rows":2}
```

Then run:

```powershell
.\.venv\Scripts\python.exe -m datawais.client --role inspector --session inspection --transcript evidence\my-session.jsonl call inspect_dataset --args-file inspect-args.json
```

Arguments are read from JSON files to avoid shell quoting errors. Transcripts
contain inputs and results; use synthetic data for the submitted demo. Server
audit logs omit argument values and tokens.

## Connect an AI host

In a host supporting remote MCP with bearer headers, create an MCP server entry:

- URL: `http://127.0.0.1:8765/mcp`, or the approved public HTTPS URL.
- Header: `Authorization: Bearer <token for the selected role>`.
- Use **inspector** for the first agent session and **cleaner** for the second.

Host configuration formats vary. `config/mcp.example.json` illustrates the
connection fields; substitute credentials locally. The included CLI client works
without configuring another desktop application. The recorded demo uses AI
agent sessions selecting real calls through this client.

Do not use the admin token for routine data work. Discovery returns only the
selected role's tools, and calling an unavailable tool is rejected server-side.

## Tools

| Tool | Inspector | Cleaner | Admin |
|---|:---:|:---:|:---:|
| list_files | yes | yes | yes |
| read_file | yes | yes | yes |
| search_files | yes | yes | yes |
| inspect_dataset | yes | yes | yes |
| validate_dataset | yes | yes | yes |
| find_duplicates | yes | yes | yes |
| write_file | reports/handoff | reports/handoff/notes | reports/handoff/notes |
| str_replace | — | yes | yes |
| create_clean_copy | — | yes | yes |
| delete_file | — | — | generated reports/notes only |

All paths are relative to the workspace. Generic writing tools accept only
`.md`, `.txt`, `.json` files in their permitted folders. They cannot edit raw
datasets, rules or cleaning outputs. Existing-file edits require the current
SHA-256; deletion also requires `confirm=true`. The cleaner checks current
dataset, rule and policy hashes and never overwrites an existing output run.

## Dataset contract

- UTF-8 CSV (optional BOM), comma delimiter, unique nonempty headers.
- Up to 5 MiB, 10,000 records and 100 columns; parser rejects malformed records.
- Quoted commas and multiline values are supported. Record numbers count parsed
  data records, not physical text lines.
- Missing means an empty/whitespace value. Values such as `N/A` remain literal
  text unless the operator explicitly handles them before the run.
- Label checks are exact and case-sensitive. Decimal fields must be finite;
  integer fields use integer syntax. Optional blank numeric values are permitted
  unless that field is declared required.
- Duplicate matching uses `duplicate_keys` or all columns, exactly as stored.
- Cleaning order: trim configured columns, apply explicit mappings, reject
  invalid records, then keep the first remaining record for each duplicate key.

`fixtures/rules/` contains the complete example schemas. Operators prepare rules
and policy before agent access; agents cannot rewrite them to make a report pass.

`create_clean_copy` accepts a `request` object with dataset/rule/policy paths,
their current SHA-256 hashes, and a unique output name. It writes an atomic run
folder containing `cleaned.csv`, `excluded.json` and `report.json`. The report
includes source hashes, counts, corrections and post-clean validation. An empty
but structurally valid output can pass the declared rules, so always inspect
record counts; passing checks does not establish model suitability or truth.

## Shared memory and demo

Read `docs/DEMO.md`. Both sessions communicate through:

- `handoff/PROJECT_STATE.md`
- `handoff/PLAN_LOG.md`
- `handoff/CHECKPOINTS.md`
- `handoff/DECISIONS.md`

The second session receives the project location and continuation objective,
then discovers its task from these files. No conversational findings from the
first agent are passed to it. `evidence/` distinguishes real agent transcripts
from scripted protocol checks.

## Process management and HTTPS deployment

Install process-management tools:

```powershell
npm install -g pm2 @modelcontextprotocol/inspector
```

Obtain the Windows `cloudflared` executable from Cloudflare's official releases.
Start locally under supervision:

```powershell
.\scripts\Start-DataWais.ps1
```

After approving public exposure, start an HTTPS quick tunnel:

```powershell
.\scripts\Start-DataWais.ps1 -CloudflaredExe 'C:\path\cloudflared.exe'
```

The script saves the public URL in `.runtime/public-url.txt`, configures the
server's exact allowed hostname and restarts it. Authentication remains required.
Quick tunnels are temporary and can change URL when restarted. A stable
presentation deployment should use an operator-owned named tunnel or static
domain. Keep the host awake; pm2 restarts processes, not a powered-off computer.
On Windows pm2 reboot startup must be configured separately; it is not installed
as a Windows service by these scripts.

```powershell
$env:PM2_HOME = Join-Path $PWD '.runtime\pm2'
pm2 status
pm2 logs datawais-server --lines 20
.\scripts\Stop-DataWais.ps1
```

The original chat's attempt to publish through Cloudflare was blocked by automatic
approval review pending explicit user consent to that destination. See the
current `evidence/STATUS.md` for the verified state; this README does not claim
that a public deployment was completed.

## Security boundaries

Only the operator may modify the workspace through the operating system. The
sandbox rejects parent traversal, absolute/UNC/drive paths, alternate streams,
hidden names, reserved device names, symlinks, junctions and reparse points.
The workspace must not be writable by untrusted local accounts: path checks are
not an OS sandbox against a hostile local process racing directory replacement.
One managed server process shares a lock across roles. Do not run multiple
independent writers against the same root.

Tokens are prototype credentials, not a full OAuth deployment. Use HTTPS for
remote access and a compatible client that supports bearer headers. Store token
files with account-restricted permissions and rotate them before sharing.
The endpoint checks hosts/origins, limits request sizes and has no command
execution tools. Dataset text is always untrusted data; host-side instruction
handling remains part of the security boundary.

## References

- [Official MCP Python SDK, v1 API](https://py.sdk.modelcontextprotocol.io/v1/)
- [MCP filesystem reference server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [Cloudflare quick tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
- [pm2 documentation](https://pm2.keymetrics.io/docs/usage/quick-start/)
