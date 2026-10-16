# Five-minute live demo

Before presenting, start the process manager, verify the endpoint and run
`scripts/check_http.py`. Use a fresh fixture workspace or a unique output name;
never overwrite past evidence. Keep the real raw files and rules read-only.

## First fresh AI session: inspector

Connect using the inspector token. Give only this objective:

> Use DataWais MCP to inspect the dataset referenced in PROJECT_STATE. Read the
> supplied validation rules and cleaning policy. Identify quality issues without
> changing data. Save findings, hashes, decisions and a continuation checkpoint
> in the shared workspace. Stop before cleaning.

Show its discovered tools, bounded results and saved handoff. For the sample
fixture expect 8 parsed records, one duplicate record, one missing required value,
one invalid label and one value needing configured whitespace trimming. A quoted
comma and a multiline value demonstrate that CSV parsing is correct.

## Second fresh AI session: cleaner

Connect with the cleaner token. Do not paste the first conversation. Give:

> Continue the DataWais dataset task using its shared handoff files. Apply only
> the supplied policy, create a new cleaned copy, validate it, verify the raw
> source is unchanged and save the final checkpoint and decisions.

Show the source hashes, cleaned output, excluded records and report. Expected
sample result: 8 input records, 6 retained, 2 excluded, one explicit label mapping,
one whitespace correction, no remaining validation issues or duplicates. Source
hash remains unchanged. The incomplete original and removed duplicate remain
visible in excluded.json with reasons.

## Timing

- 0:00–0:40: problem, server, real MCP discovery.
- 0:40–2:00: inspector's calls and findings.
- 2:00–2:30: show shared memory and switch session.
- 2:30–4:15: cleaner's continuation and verified outputs.
- 4:15–5:00: show blocked traversal, immutable source, audit and architecture.

The included SDK client can be operated by an AI agent through a terminal. This
is how the chat demonstration was executed. It is not itself an autonomous LLM.
The automated HTTP check is separate from the real agent demonstration.

## Questions to prepare for

- Why MCP? A host discovers and invokes schema-described tools using the protocol.
- Why file-server tools? They are the connector foundation and persist handoff.
- Why deterministic validation? Results follow declared rules and can be tested.
- Why separate roles? Inspectors cannot clean or delete; cleaners cannot delete.
- What if an input changes? Stale hashes reject cleaning; the agent must re-read.
- What does “valid” mean? It satisfies the configured rules, not every ML concern.
- What is still limited? CSV scale, prototype token auth, local OS trust, tunnel
  availability and no statistical bias or semantic truth checking.
