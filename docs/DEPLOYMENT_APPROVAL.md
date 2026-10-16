# Prepared HTTPS deployment

**Completed:** the user authorized finishing setup after the specific deployment
request. Cloudflare publication and public MCP verification have now completed.
This file retains the reviewed exposure description; current results are in
`evidence/STATUS.md`.

The local connector and process manager are already working. The remaining
deployment action is to start the downloaded Cloudflare Tunnel executable under
the same isolated pm2 instance and point it at `http://127.0.0.1:8765`.

## What would be exposed

- One authenticated MCP endpoint at a generated `https://*.trycloudflare.com/mcp` URL.
- A public health check containing only the service name and status.
- The MCP tools' accessible data is restricted to this project's `workspace/`.
- That workspace contains a synthetic eight-record university question dataset,
  rule files, synthetic outputs, and the demo's shared state/reports.
- Project source, `.runtime/secrets.json`, the user's Downloads and all other
  folders are outside the MCP workspace and cannot be read through its tools.

## Access and remaining risks

Remote MCP calls require a random role-specific bearer token. A URL alone does
not grant tool access. Inspectors cannot clean or delete, cleaners cannot delete,
and no role can overwrite raw data or rules. Host and origin checks will include
only the actual tunnel hostname.

Cloudflare operates the external destination and handles tunneled traffic.
Anyone obtaining a valid token could exercise that role's permitted tools. A
quick-tunnel URL is temporary and has no uptime guarantee. No real university
student records have been loaded for this demonstration.

Automatic approval review rejected starting this tunnel because general
deployment authorization did not specify the external destination and exposed
workspace. It has not been started by another route. The requested approval is
specifically to publish this synthetic demo through Cloudflare with the existing
authentication and sandbox controls.
