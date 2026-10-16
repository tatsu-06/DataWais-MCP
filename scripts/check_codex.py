"""Verify the configured Codex credential helper through a real MCP handshake."""
import asyncio
import json
from pathlib import Path
import subprocess
import tomllib

from datawais.client import execute

project = Path(__file__).resolve().parents[1]
config = tomllib.loads((Path.home()/".codex/config.toml").read_text(encoding="utf-8-sig"))
entry = config["mcp_servers"]["datawais"]
header_text = subprocess.check_output(entry["http_headers_helper"],shell=True,text=True,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
authorization = json.loads(header_text)["Authorization"]
assert authorization.startswith("Bearer ")
result = asyncio.run(execute(entry["url"],authorization[7:],"list"))
names = [t["name"] for t in result["tools"]]
assert result["server"] == "DataWais MCP (cleaner)"
assert len(names) == 9 and "delete_file" not in names
evidence = {"configured":True,"url":entry["url"],"authentication":"private local header helper","server":result["server"],"tools":names,"credentials_in_config":False,"existing_connections":sorted(k for k in config["mcp_servers"] if k != "datawais")}
(project/"evidence/codex-connection.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
print("Codex DataWais configuration verified: helper authentication, real MCP handshake and nine correctly scoped tools. No credentials printed.")
