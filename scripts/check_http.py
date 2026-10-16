"""Live protocol/security verification; distinct from the autonomous agent demo."""
import argparse
import asyncio
import json
from pathlib import Path
import ipaddress
import socket
from urllib.parse import urlsplit

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765/mcp")
    parser.add_argument("--output", type=Path, default=Path("evidence/http-checks.json"))
    parser.add_argument("--resolved-ip", help="Optional independently verified DNS answer for this URL only; TLS still verifies the original hostname.")
    args = parser.parse_args()
    if args.resolved_ip:
        ipaddress.ip_address(args.resolved_ip)
        target = urlsplit(args.url).hostname
        original_resolver = socket.getaddrinfo
        def resolve_target(host,port,*positional,**keywords):
            name = host.decode("ascii") if isinstance(host,bytes) else host
            return original_resolver(args.resolved_ip if name == target else host,port,*positional,**keywords)
        socket.getaddrinfo = resolve_target
    tokens = json.loads(Path(".runtime/secrets.json").read_text())["tokens"]
    checks = []
    async with httpx.AsyncClient(timeout=30) as client:
        for headers, label in [({}, "missing token rejected"), ({"Authorization":"Bearer invalid"}, "invalid token rejected"), ({b"Authorization":b"Bearer \xff"}, "non-ASCII token rejected")]:
            response = await client.post(args.url, headers=headers, json={})
            assert response.status_code == 401
            checks.append(label)
        response = await client.post(args.url, headers={"Authorization":f"Bearer {tokens['admin']}", "Origin":"https://evil.example"}, json={})
        assert response.status_code == 403, response.text
        checks.append("untrusted Origin rejected")
    for role in tokens:
        async with httpx.AsyncClient(headers={"Authorization":f"Bearer {tokens[role]}"}, timeout=60) as http:
            async with streamable_http_client(args.url, http_client=http) as (read,write,_):
                async with ClientSession(read,write) as session:
                    await session.initialize()
                    tools = {t.name for t in (await session.list_tools()).tools}
                    assert len(tools) == {"admin":10,"inspector":7,"cleaner":9}[role]
                    checks.append(f"{role}: correct {len(tools)}-tool scope")
                    schemas = await session.list_tools()
                    assert all(t.inputSchema.get("additionalProperties") is False for t in schemas.tools)
                    invalid = await session.call_tool("list_files", {"unexpected":True})
                    assert invalid.isError
                    checks.append(f"{role}: strict schemas reject extra arguments")
                    invalid = await session.call_tool("read_file", {"path":"../.runtime/secrets.json"})
                    assert invalid.isError
                    invalid = await session.call_tool("read_file", {"path":"handoff/PROJECT_STATE.md", "limit":32001})
                    assert invalid.isError
                    invalid = await session.call_tool("write_file", {"path":"datasets/raw/university_questions.csv", "content":"bad"})
                    assert invalid.isError
                    checks.append(f"{role}: traversal, oversized read and raw write rejected")
                    if role == "inspector":
                        invalid = await session.call_tool("create_clean_copy", {"request":{}})
                        assert invalid.isError
                        checks.append("inspector cannot call cleaner tool by guessing its name")
                    if role == "admin":
                        created = await session.call_tool("write_file", {"path":"notes/http-check.txt", "content":"a unique marker"})
                        assert not created.isError
                        sha = created.structuredContent["sha256"]
                        changed = await session.call_tool("str_replace", {"path":"notes/http-check.txt", "old_str":"unique", "new_str":"verified", "expected_sha256":sha})
                        assert not changed.isError
                        sha = changed.structuredContent["sha256"]
                        denied = await session.call_tool("delete_file", {"path":"notes/http-check.txt", "expected_sha256":sha})
                        assert denied.isError
                        deleted = await session.call_tool("delete_file", {"path":"notes/http-check.txt", "expected_sha256":sha,"confirm":True})
                        assert not deleted.isError
                        checks.append("write, exact replacement and gated delete work over MCP")
                    resource = await session.read_resource("datawais://project-state")
                    assert resource.contents
                    prompts = await session.list_prompts()
                    assert prompts.prompts[0].name == "continue_dataset_task"
                    checks.append(f"{role}: resource and prompt available")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"url":args.url,"passed":len(checks),"checks":checks,"dns_override":args.resolved_ip,"tls_hostname_verification":True},indent=2))
    print(f"PASS: {len(checks)} protocol/security checks; saved {args.output}")


asyncio.run(main())
