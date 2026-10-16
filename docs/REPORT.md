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
manages the process and a configured HTTPS tunnel can expose it after approval.

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

The report does not claim public deployment or model accuracy improvements
without corresponding evidence. Publication through Cloudflare requires the
specific approval requested by automatic review in this chat.

## Verification and evidence

Core tests cover traversal and reserved paths, symlinks, immutable files, stale
versions, exact-match replacement, guarded deletion, malformed CSV, quoted commas,
multiline values, duplicate survivors and numeric validation. Live MCP checks
cover authentication, origin checks, scoped tools, schemas, error results,
resources, prompts and core writing operations.

See `evidence/STATUS.md` for actual run results and the remaining deployment step.
