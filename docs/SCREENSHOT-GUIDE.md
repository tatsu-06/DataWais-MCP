# Prepare your own DataWais documentation

## Start here

1. Open the project folder on the original computer.
2. Double-click START-DATAWAIS.cmd and allow the service check to finish.
   Its window stays open so you can read the success message or any error.
   After success, closing that window does not stop the background services.
3. Double-click DOCUMENTATION.cmd. This opens a menu of real results for screenshots.
4. Choose a menu number and use Windows + Shift + S to capture the relevant area.
5. Save screenshots in order and add a short explanation beneath each in Word or Google Docs.

The helper queries the real MCP server. It does not clean data, fabricate results,
or create new AI agent sessions. Its saved-session view is labeled as recorded
evidence. Do not call a failed or incomplete check a successful result.

## Recommended screenshots

| Figure | What to capture | What to explain |
|---|---|---|
| 1 Repository | Public GitHub page showing the project, README, src, tests, docs and evidence | Where the implementation and reproducible evidence are stored |
| 2 Running deployment | Documentation menu 6 deployment | Server and HTTPS tunnel are online under pm2; remote access needs this computer online |
| 3 MCP tools | Menu 1 tools | Tools are discovered through MCP; admin has 10, inspector 7 and cleaner 9 |
| 4 Original dataset | Menu 2 before | Eight records contain missing data, an invalid label and one duplicate |
| 5 Shared memory | Menu 3 handoff plus the four files in the repository | PROJECT_STATE, PLAN_LOG, CHECKPOINTS and DECISIONS preserve context |
| 6 Two sessions | Your two actual fresh client conversations, or clearly label menu 7 as the recorded run | The continuation uses shared files rather than a pasted copy of the first conversation |
| 7 Cleaned results | Menu 4 after | Six records remain, two are excluded, validation passes and the source hash is unchanged |
| 8 Security | Menu 5 security | A missing token is rejected and a path outside the workspace is blocked |
| 9 Tests | Menu 8 test execution | Show the actual pass count from the run and state what the tests cover |

You can combine deployment and tool screenshots if the document becomes long.
Use readable crops; do not shrink a full desktop into an unreadable image.

## How to show a fresh two session run

Use two fresh AI conversations connected to DataWais. Do not paste the first
conversation into the second. The original transcript demonstrates server-enforced
inspector and cleaner roles through the SDK client; the configured Codex
connection uses the cleaner role. Saying “act as inspector” alone does not change
server permissions. For a strict role-scoped demonstration, use clients configured
with the actual inspector token for session one and cleaner token for session two.

### Session one prompt

> Use DataWais MCP to start a new documentation demonstration on
> datasets/raw/university_questions.csv. Read the existing state, then inspect and
> validate the original against rules/questions.json. Read the supplied
> rules/cleaning_policy.json. Do not clean data. Save findings, the three current
> input hashes, a plan and an explicit continuation instruction in the four
> handoff files. Choose an unused output name based on the current time, record
> it in PROJECT_STATE and stop. Use the tools and preserve the original.

Capture the actual tool calls, findings and successful handoff writes. The source
has eight records; do not claim the cleaned result before the second session runs.

### Session two prompt

> Continue the DataWais task using only its shared handoff files. Read
> PROJECT_STATE, PLAN_LOG, CHECKPOINTS and DECISIONS. Verify the dataset, rules and
> policy hashes, then use the unused output name recorded in the handoff to create
> a cleaned copy. Independently validate it, check duplicates and verify that the
> original source hash is unchanged. Save the final report and updated handoff.
> Do not guess mappings or overwrite an existing output run.

Capture the new session reading shared state before cleaning, then its successful
creation, validation and source-preservation check. A fresh output name is
required because pt1-demo-1 already exists. If you create a new run, record its
exact path in your captions; menu 4 intentionally verifies the original recorded
pt1-demo-1 output and is not evidence of the new run.

## Suggested document structure

1. Project title and repository link.
2. Problem and objectives in your own words.
3. Architecture: user, AI host and MCP client, DataWais server, protected files.
4. Tool design and role access, with the tools screenshot.
5. Dataset workflow and two-session handoff, with before, handoff and after figures.
6. Security and validation tests, with rejection and test screenshots.
7. Results, limits and what you learned.

Below each figure, write what you did, what the image shows and why it matters.
Example: “Figure 7 shows six valid records after the explicit cleaning policy was
applied. The original SHA-256 matches the report, so cleaning preserved the source.”

## Short explanation for the professor

“DataWais is our MCP file-server connector for dataset preparation. The AI client
discovers tools and calls them through MCP. One session inspects the dataset and
saves its progress in shared files. A fresh session reads those files and
continues the cleaning task. The server enforces access rules, preserves the raw
data and records what changed.”

Be prepared to explain why this is MCP, which component chooses tools, how paths
are protected, why role scope matters, how version guards work and what passing
validation does and does not prove.

## Capture honestly and keep credentials private

- Capture actual runs; preserve visible errors and describe their resolution.
- Never photograph .runtime/secrets.json, public-clients.json, token values or Authorization headers.
- The screenshot helper deliberately omits tokens and private configuration contents.
- Keep the source data synthetic for the classroom demonstration.
- Screenshots support the code, transcripts and live demo; they do not replace them.

Export your final document as a PDF under the form's 10 MB limit. The existing
seven-page submission PDF can be used as a reference; rewrite explanations to
reflect your understanding and the runs you actually capture.
