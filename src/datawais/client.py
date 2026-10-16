"""A real SDK-based MCP client. Agents choose calls through this CLI.

This is not itself an LLM agent. The demo transcript labels scripted checks and
human/agent-selected operations separately.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def execute(url, token, operation, tool=None, arguments=None):
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}, timeout=60, follow_redirects=False) as http:
        async with streamable_http_client(url, http_client=http) as (read, write, _):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                if operation == "list":
                    result = await session.list_tools()
                    return {"server": initialized.serverInfo.name, "tools": [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in result.tools]}
                if operation == "resource":
                    result = await session.read_resource("datawais://project-state")
                elif operation == "prompts":
                    result = await session.list_prompts()
                else:
                    result = await session.call_tool(tool, arguments or {})
                return result.model_dump(mode="json", by_alias=True, exclude_none=True)


def main():
    parser = argparse.ArgumentParser(description="DataWais real MCP client")
    parser.add_argument("--url", default=os.environ.get("DATAWAIS_URL", "http://127.0.0.1:8765/mcp"))
    parser.add_argument("--secrets", type=Path, default=Path(".runtime/secrets.json"))
    parser.add_argument("--role", choices=["admin", "inspector", "cleaner"], default="inspector")
    parser.add_argument("--session", default="manual")
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("operation", choices=["list", "call", "resource", "prompts"])
    parser.add_argument("tool", nargs="?")
    parser.add_argument("--args-file", type=Path)
    args = parser.parse_args()
    token = json.loads(args.secrets.read_text(encoding="utf-8"))["tokens"][args.role]
    arguments = json.loads(args.args_file.read_text(encoding="utf-8")) if args.args_file else {}
    if args.operation == "call" and not args.tool:
        parser.error("call requires a tool name")
    result = asyncio.run(execute(args.url, token, args.operation, args.tool, arguments))
    if args.transcript:
        args.transcript.parent.mkdir(parents=True, exist_ok=True)
        event = {"time": datetime.now(timezone.utc).isoformat(), "session": args.session, "role": args.role, "transport": "MCP Streamable HTTP", "operation": args.operation, "tool": args.tool, "arguments": arguments, "result": result}
        with args.transcript.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False)+"\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
