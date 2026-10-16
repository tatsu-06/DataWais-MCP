"""Keep a managed quick-tunnel hostname synchronized with the MCP server."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

DOMAIN = re.compile(r"https://([a-z0-9]+(?:-[a-z0-9]+)*\.trycloudflare\.com)(?:[/\s]|$)")


def configure_hostname(hostname: str, runtime: Path) -> None:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.trycloudflare\.com", hostname):
        raise ValueError("Unexpected Cloudflare quick-tunnel hostname")
    runtime.mkdir(parents=True, exist_ok=True)
    url = f"https://{hostname}/mcp"
    tokens = json.loads((runtime/"secrets.json").read_text())["tokens"]
    servers = {f"datawais-{role}": {"type":"streamable-http", "url":url, "headers":{"Authorization":"Bearer "+token}} for role,token in tokens.items()}
    # Publish the URL last; client files containing credentials stay private.
    for filename,text in [("public-host.txt",hostname), ("public-clients.json",json.dumps({"mcpServers":servers},indent=2)), ("public-url.txt",url)]:
        target = runtime/filename
        temp = target.with_suffix(target.suffix+".tmp")
        temp.write_text(text,encoding="utf-8")
        os.replace(temp,target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cloudflared", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--pm2", required=True)
    parser.add_argument("--runtime", type=Path, default=Path(".runtime"))
    args = parser.parse_args()
    command = [args.cloudflared,"tunnel","--url","http://127.0.0.1:8765","--no-autoupdate","--protocol","http2"]
    child = subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    last_host = None
    try:
        for line in child.stdout:
            print(line.rstrip(),file=sys.stderr,flush=True)
            match = DOMAIN.search(line)
            if match and match.group(1) != last_host:
                last_host = match.group(1)
                configure_hostname(last_host,args.runtime)
                environment = dict(os.environ,DATAWAIS_PUBLIC_HOST=last_host)
                result = subprocess.run([args.node,args.pm2,"restart","datawais-server","--update-env"],env=environment,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                if result.returncode:
                    raise RuntimeError("Could not synchronize the MCP server hostname")
                print(f"DataWais endpoint synchronized: https://{last_host}/mcp",flush=True)
        raise SystemExit(child.wait() or 1)
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()


if __name__ == "__main__":
    main()
