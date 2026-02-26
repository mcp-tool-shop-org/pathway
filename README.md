<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  
            <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/pathway/readme.png"
           alt="Pathway logo" width="400">
</p>

<p align="center">
    <em>Append-only journey engine where undo never erases learning.</em>
</p>

<p align="center">
    <a href="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml">
        <img src="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml/badge.svg" alt="CI">
    </a>
    <a href="https://pypi.org/project/mcpt-pathway/">
        <img src="https://img.shields.io/pypi/v/mcpt-pathway" alt="PyPI version">
    </a>
    <a href="https://opensource.org/licenses/MIT">
        <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
    </a>
    <a href="https://mcp-tool-shop-org.github.io/pathway/">
        <img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page">
    </a>
</p>

**Pathway Core is an append-only journey engine where undo never erases learning.**

Undo is navigation. Learning persists.

## Philosophy

Traditional undo rewrites history. Pathway doesn't.

When you backtrack in Pathway, you create a new event pointing backward—the original path remains. When you learn something on a failed path, that knowledge persists. Your mistakes teach you; they don't disappear.

This makes Pathway fundamentally honest about what happened.

## Features

- **Append-only event log**: Events are never edited or deleted
- **Undo = pointer move**: Backtracking creates a new event and moves head
- **Learning persists**: Knowledge survives across backtracking and branches
- **Branching is first-class**: Git-like implicit divergence on new work after backtrack

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Initialize database
python -m pathway.cli init

# Import sample session
python -m pathway.cli import sample_session.jsonl

# View derived state
python -m pathway.cli state sess_001

# Start API server
python -m pathway.cli serve
```

## API Endpoints

- `POST /events` - Append an event
- `GET /session/{id}/state` - Get derived state (JourneyView, LearnedView, ArtifactView)
- `GET /session/{id}/events` - Get raw events
- `GET /sessions` - List all sessions
- `GET /event/{id}` - Get single event

## Event Types

14 event types covering the full journey lifecycle:

| Type | Purpose |
|------|---------|
| IntentCreated | User's goal and context |
| TrailVersionCreated | The learning path/map |
| WaypointEntered | Navigation through trail |
| ChoiceMade | User makes a branching decision |
| StepCompleted | User completes a waypoint |
| Blocked | User hits friction |
| Backtracked | User goes back (undo) |
| Replanned | Trail is revised |
| Merged | Branches converge |
| ArtifactCreated | Output produced |
| ArtifactSuperseded | Old output replaced |
| PreferenceLearned | How user likes to learn |
| ConceptLearned | What user understands |
| ConstraintLearned | User's environment facts |

## Derived Views

The system computes three views from events:

1. **JourneyView**: Current position, branches, visited waypoints
2. **LearnedView**: Preferences, concepts, constraints with confidence scores
3. **ArtifactView**: All outputs with supersedence tracking

## Security

- **API key**: Set `PATHWAY_API_KEY` env var to protect write endpoints
- **Payload limit**: 1MB default (configure via `PATHWAY_MAX_PAYLOAD_SIZE`)
- **Session ID validation**: Alphanumeric + underscore/hyphen, max 128 chars

## Testing

```bash
pytest  # 73 tests covering invariants, API, reducers, store
```

## Architecture

```
pathway/
├── models/         # Pydantic models for events and views
├── store/          # SQLite event store + JSONL import/export
├── reducers/       # Compute derived views from events
├── api/            # FastAPI endpoints
└── cli.py          # Command-line tools
```
