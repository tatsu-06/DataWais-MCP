# DataWais MCP — technical report

## Problem and implementation

DataWais is a sandboxed MCP file-server connector extended with deterministic CSV
inspection, validation, duplicate detection and cleaning. Persistent handoff
files allow a fresh agent session to resume work without the earlier chat.

## Stack choices

Python keeps CSV processing and file operations in one runtime. The official
MCP Python SDK 1.30.0 is pinned so generated schemas and transport behavior remain
reproducible. This project deliberately uses the v1 SDK API; follow the v1 docs
when maintaining it. Typed input models reject unknown properties and invalid
types. The standard CSV parser handles quoted delimiters and embedded newlines.
Streamable HTTP supports a standalone endpoint. Uvicorn serves locally, pm2
manages the process and the configured HTTPS tunnel exposes the authenticated
endpoint. The managed server receives its three role tokens through environment
variables. An ignored private JSON file provisions the local tokens and supports
direct development runs; credentials are never embedded in source or shared ZIPs.

## Tool design

Each tool has one purpose, an explanatory description and a strict schema.
Inspection returns counts, hashes and bounded samples; search returns excerpts;
validation returns aggregate counts and limited examples. Model context does not
need to contain whole datasets. File overwrites require a fresh hash. Cleaning
requires hashes of all three inputs and creates an immutable output run.

One resource exposes project state, and one prompt provides a continuation
workflow. They complement the ten tools without replacing the handoff files.

## Agent management and efficiency

Roles are enforced by separate server tool registries selected from bearer
credentials. Inspector has seven tools, cleaner nine, admin ten. The normal demo
uses inspector and cleaner sequentially. Each agent reads before editing,
records its state and has a clear stop condition. The server logs requests even
when argument validation rejects them; completed handler calls log outcomes and
duration without content or credentials. Agent-selected transcripts record the
actual evidence for the demonstration.

The server is stateless at the HTTP session layer. Shared project state lives in
files, so it survives an agent disconnect or a server process restart. HTTP
connection sessions and AI conversation sessions are different concepts; the
demonstration uses two distinct AI agent contexts.

## Security tradeoffs

Workspace path checks and immutable raw/rule folders restrict agent actions.
Links and Windows reparse points are rejected. One in-process lock serializes
writes, and cleaned outputs are published by renaming a completed staging folder.
The design assumes a trusted local filesystem owner and one server process;
it does not defeat a hostile local user racing directory changes or provide
cross-process locking. A crash can leave an ignored hidden staging directory.

Role tokens are suitable for this prototype; OAuth, per-user revocation and
rate limiting are future improvements. The public endpoint needs HTTPS and
authentication. Dataset text must never be interpreted as instructions.

Public deployment was completed after user authorization. A managed tunnel
wrapper synchronizes the exact host allowlist and private client configurations
when Cloudflare assigns a new URL. An initial router DNS-cache issue has resolved;
all public checks now pass using normal DNS with TLS verification. Codex uses
the stable local endpoint with a private credential helper; native MCP calls
from this chat have also succeeded.
No model accuracy improvements are claimed from validation alone.

## Verification and evidence

Core tests cover traversal and reserved paths, symlinks, immutable files, stale
versions, exact-match replacement, guarded deletion, malformed CSV, quoted commas,
multiline values, duplicate survivors and numeric validation. Live MCP checks
cover authentication, origin checks, scoped tools, schemas, error results,
resources, prompts and core writing operations.

See `evidence/STATUS.md` for actual run results and `docs/PT1-CHECKLIST.md` for
submission and live-presentation steps that remain.
