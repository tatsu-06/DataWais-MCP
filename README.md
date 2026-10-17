# DataWais MCP

A sandboxed MCP file server for CSV dataset inspection, validation and controlled cleaning.

DataWais exposes file and dataset tools over MCP Streamable HTTP. It preserves raw
datasets, applies operator-supplied rules and cleaning policies, and saves task
state so another AI session can continue the work. The server does not call a
model API itself.

## Install and run on Windows

Install Python 3.11 or later and Node.js for optional process management.
From the project directory, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe scripts\init_demo.py
.\.venv\Scripts\python.exe -m datawais.server
```

The initializer creates a sample `workspace/` and private credentials in
`.runtime/secrets.json`. It refuses to overwrite an existing workspace.
Both folders are excluded from Git.

The MCP endpoint is `http://127.0.0.1:8765/mcp`. A bearer token is required.
The health endpoint is `http://127.0.0.1:8765/healthz`.

On an already configured installation, use `START-DATAWAIS.cmd` and
`STOP-DATAWAIS.cmd`. A downloaded source copy needs the installation steps first.

## Connect an MCP client

Configure a client that supports Streamable HTTP and an Authorization header:

- URL: `http://127.0.0.1:8765/mcp`, or the deployed HTTPS endpoint.
- Header: `Authorization: Bearer <token for the chosen role>`.
- Example configuration: `config/mcp.example.json`.

Store real credentials locally. Never commit tokens or private client settings.
The included SDK client can discover tools directly:

```powershell
.\.venv\Scripts\python.exe -m datawais.client --role cleaner list
```

## Tools and permissions

| Tool | Inspector | Cleaner | Admin |
|---|:---:|:---:|:---:|
| list_files | yes | yes | yes |
| read_file | yes | yes | yes |
| search_files | yes | yes | yes |
| inspect_dataset | yes | yes | yes |
| validate_dataset | yes | yes | yes |
| find_duplicates | yes | yes | yes |
| write_file | restricted | restricted | restricted |
| str_replace | no | yes | yes |
| create_clean_copy | no | yes | yes |
| delete_file | no | no | restricted |

The server exposes seven inspector tools, nine cleaner tools and ten admin tools.
Roles are enforced using credentials, rather than instructions in an AI prompt.

## Dataset workflow

1. Inspect a CSV and validate it against an operator-supplied rules file.
2. Check duplicates and read the supplied cleaning policy.
3. Save findings, input hashes and a continuation plan in the four handoff files.
4. In a fresh session, read the handoff and verify the source, rules and policy hashes.
5. Call `create_clean_copy` with those hashes and an unused output name.
6. Independently validate the cleaned result and confirm that the raw source is unchanged.

Task memory lives in `handoff/PROJECT_STATE.md`, `PLAN_LOG.md`, `CHECKPOINTS.md`
and `DECISIONS.md` within the workspace. The fixture files provide a starting point.

Cleaning creates a new folder containing `cleaned.csv`, `excluded.json` and
`report.json`. It trims configured fields, applies explicit mappings, excludes
invalid records and retains the first valid record for each duplicate key.
It never overwrites an existing output run or changes the original dataset.

CSV input is bounded to 5 MiB, 10,000 records and 100 columns. Quoted commas and
embedded newlines are supported. Inspection returns at most five sample rows.
Passing validation establishes compliance with the declared rules, rather than
factual correctness or suitability for training a model.

## Process management and HTTPS

Install PM2 and obtain the Cloudflare `cloudflared` executable, then run:

```powershell
npm install -g pm2
.\scripts\Start-DataWais.ps1 -CloudflaredExe 'C:\path\cloudflared.exe'
```

PM2 supervises the server and tunnel. The current public endpoint is saved in
`.runtime/public-url.txt`. Authentication remains required. Quick-tunnel addresses
can change after restart; the tunnel wrapper updates the server hostname allowlist
and private connection settings. The host computer must remain awake and online.

`scripts/Install-Autostart.ps1` installs current-user sign-in startup.
`DISABLE-AUTOSTART.cmd` disables it.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\check_http.py
```

The tests cover filesystem restrictions, roles, hash guards, CSV processing,
credentials and tunnel configuration. The HTTP check requires a running server.

## Security boundaries

Paths must stay within the workspace. The server rejects traversal, absolute and
UNC paths, hidden names, reserved device names, alternate streams, symlinks,
junctions and reparse points. Generic writes are limited to permitted text folders.
Raw data and operator rules are protected from agent writes. Updates require
current hashes; deletion also requires admin scope and explicit confirmation.

Use HTTPS for remote access. Tokens are prototype credentials rather than a full
OAuth deployment. The implementation assumes a trusted local machine owner and
a single writer process. Dataset text is treated as data, never as instructions.
