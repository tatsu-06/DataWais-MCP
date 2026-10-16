"""Add one authenticated DataWais connection, preserving existing Codex config.

Use the desktop application's current Codex runtime. Older global CLI releases
may not support http_headers_helper; the standalone MCP client remains available.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tomllib

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=Path, required=True)
parser.add_argument("--url", default="http://127.0.0.1:8765/mcp")
args = parser.parse_args()
project = Path(__file__).resolve().parents[1]
existing = args.config.read_text(encoding="utf-8-sig") if args.config.exists() else ""
parsed = tomllib.loads(existing)
if "datawais" in parsed.get("mcp_servers", {}):
    raise SystemExit("DataWais is already configured; no existing connection was overwritten.")
helper = f'powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{project / "scripts/Get-DataWaisHeaders.ps1"}" -Role cleaner'
addition = "\n\n[mcp_servers.datawais]\n" + f"url = {json.dumps(args.url)}\nhttp_headers_helper = {json.dumps(helper)}\nstartup_timeout_sec = 30\ntool_timeout_sec = 60\nenabled = true\n"
combined = existing.rstrip()+addition
updated = tomllib.loads(combined)
assert set(parsed.get("mcp_servers", {})) <= set(updated["mcp_servers"])
runtime = project/".runtime"
runtime.mkdir(exist_ok=True)
backup = runtime/("codex-config-before-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+".toml")
if args.config.exists():
    shutil.copyfile(args.config, backup)
args.config.parent.mkdir(parents=True, exist_ok=True)
args.config.write_text(combined, encoding="utf-8")
print("Added DataWais to Codex with a local credential helper. Existing connections preserved; no token written into the config.")
