---
title: API Reference
description: REST endpoints, derived views, and project architecture.
sidebar:
  order: 4
---

Pathway exposes a FastAPI-based REST API for programmatic access to the event log and derived views.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/events` | Append an event to the log |
| `GET` | `/session/{id}/state` | Get derived state (JourneyView, LearnedView, ArtifactView) |
| `GET` | `/session/{id}/events` | Get raw events for a session |
| `GET` | `/sessions` | List all sessions |
| `GET` | `/event/{id}` | Get a single event by ID |

### Authentication

Set the `PATHWAY_API_KEY` environment variable to protect write endpoints with bearer token authentication. When set, `POST /events` requires an `Authorization: Bearer <key>` header.

### Payload limits

The default maximum request body size is 1 MB. Override with `PATHWAY_MAX_PAYLOAD_SIZE` (in bytes).

### Session ID validation

Session IDs must be alphanumeric with underscores and hyphens, maximum 128 characters.

## Derived views

The `/session/{id}/state` endpoint returns three computed views:

### JourneyView
Current position in the journey, active branches, and visited waypoints. This view answers "where am I and where have I been?"

### LearnedView
Accumulated preferences, concepts, and constraints with confidence scores. Learning events from all branches (including abandoned ones) contribute to this view.

### ArtifactView
All outputs produced during the journey with supersedence tracking. Shows which artifacts are current and which have been replaced.

## Architecture

```
pathway/
├── models/         # Pydantic models for events and views
├── store/          # SQLite event store + JSONL import/export
├── reducers/       # Compute derived views from events
├── api/            # FastAPI endpoints
└── cli.py          # Command-line tools
```

### Models
Pydantic models define the schema for all 14 event types and the three derived views. Events are validated on ingestion.

### Store
The SQLite event store provides append-only writes with JSONL import/export for bulk operations.

### Reducers
Pure functions that fold an event stream into derived views. Each reducer handles a specific view (journey, learned, artifact).

### API
FastAPI endpoints expose the store and reducers over HTTP with authentication, validation, and payload limits.

## Security

| Aspect | Detail |
|--------|--------|
| **Data touched** | Journey events and derived views in local SQLite |
| **Data NOT touched** | No telemetry, no analytics, no credential storage |
| **Permissions** | Read/write to local SQLite database |
| **Network** | Localhost HTTP server only — no outbound calls |
| **Telemetry** | None collected or sent |
