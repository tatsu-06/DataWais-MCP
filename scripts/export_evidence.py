"""Create a portable, credential-free snapshot and readable agent-call index."""
from collections import Counter
import json
from pathlib import Path
import shutil

project = Path(__file__).resolve().parents[1]
evidence = project/"evidence"
transcripts = []
summary = []
for filename in ["agent-1-transcript.jsonl", "agent-2-transcript.jsonl"]:
    path = evidence/filename
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not events:
        raise SystemExit(f"Empty transcript: {filename}")
    transcripts.append(events)
    calls = [e for e in events if e["operation"] == "call"]
    summary.append({"session":events[0]["session"], "role":events[0]["role"], "protocol_exchanges":len(events), "tool_calls":len(calls), "tool_errors":sum(bool(e["result"].get("isError")) for e in calls), "tools":dict(Counter(e["tool"] for e in calls))})
assert summary[0]["session"] != summary[1]["session"]

# Preserve the first handoff from its actual successful tool-call arguments,
# rather than taking a later filesystem snapshot after the continuation.
for event in transcripts[0]:
    if event["tool"] == "write_file" and not event["result"].get("isError"):
        args = event["arguments"]
        rel = Path(args["path"])
        if rel.parts[0] == "handoff" and len(rel.parts) == 2:
            dest = evidence/"agent-1-handoff"/rel.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(args["content"], encoding="utf-8")

for folder in ["handoff", "datasets", "rules", "reports"]:
    source = project/"workspace"/folder
    if source.exists():
        shutil.copytree(source, evidence/"completed-workspace"/folder, dirs_exist_ok=True)

audit = project/".runtime/tool-calls.jsonl"
if audit.exists():
    shutil.copyfile(audit, evidence/"server-audit.jsonl")
(evidence/"agent-session-summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
lines = ["# Actual two-session MCP demonstration", "", "Two fresh AI agent contexts selected the following real MCP calls through the", "official Python SDK client. This is distinct from scripts/check_http.py.", "", "The second agent was not given the first conversation or its findings. Its", "task instructions directed it to discover and continue from shared handoff.", ""]
for info,events in zip(summary,transcripts):
    lines += [f"## {info['session']} ({info['role']})", "", f"{info['tool_calls']} tool calls; {info['tool_errors']} tool errors.", "", "| # | Operation | Tool | Result |", "|---|---|---|---|"]
    for number,event in enumerate(events,1):
        result = "error" if event["result"].get("isError") else "success"
        lines.append(f"| {number} | {event['operation']} | {event['tool'] or 'discovery'} | {result} |")
    lines.append("")
lines += ["## Read the evidence", "", "- agent-1-transcript.jsonl and agent-2-transcript.jsonl: complete inputs/results.", "- agent-1-handoff/: the first agent's saved continuation instructions.", "- completed-workspace/: the verified final files, rules and dataset outputs.", "- server-audit.jsonl: server-side request/handler records, without credentials.", "- inspector-tools.json and inspector-inspection.json: official Inspector results.", "- http-checks.json: scripted protocol/security verification, not an agent run.", "", "All dataset records in this package are synthetic demonstration data."]
(evidence/"DEMONSTRATION.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps(summary,indent=2))
