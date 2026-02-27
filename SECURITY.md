# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

Email: **64996768+mcp-tool-shop@users.noreply.github.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Version affected
- Potential impact

### Response timeline

| Action | Target |
|--------|--------|
| Acknowledge report | 48 hours |
| Assess severity | 7 days |
| Release fix | 30 days |

## Scope

Pathway is an **append-only journey engine** with a FastAPI-based REST API.

- **Data touched:** Journey events and derived views stored in a local SQLite database. API request/response payloads (JSON)
- **Data NOT touched:** No telemetry. No analytics. No credential storage. No user PII beyond session IDs
- **Permissions:** Read/write: local SQLite database file. Network: localhost HTTP server (FastAPI/uvicorn) for API endpoints
- **Network:** Localhost API server only. No outbound network calls. No external service dependencies
- **Telemetry:** None collected or sent

### Security controls

- API key protection for write endpoints (`PATHWAY_API_KEY` env var)
- Payload size limit (1MB default, configurable)
- Session ID validation (alphanumeric + underscore/hyphen, max 128 chars)
- Append-only event store — events are never edited or deleted
