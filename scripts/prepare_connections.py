"""Generate private ready-to-use client configurations. Never print credentials."""
import json
from pathlib import Path

project = Path(__file__).resolve().parents[1]
runtime = project/".runtime"
url = (runtime/"public-url.txt").read_text().strip()
tokens = json.loads((runtime/"secrets.json").read_text())["tokens"]
servers = {f"datawais-{role}": {"type":"streamable-http", "url":url, "headers":{"Authorization":"Bearer "+token}} for role,token in tokens.items()}
(runtime/"public-clients.json").write_text(json.dumps({"mcpServers":servers},indent=2),encoding="utf-8")
print("Private connection files prepared. Public endpoint:",url)
