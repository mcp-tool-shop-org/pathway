---
title: Getting Started
description: Install Pathway and run your first journey session.
sidebar:
  order: 1
---

Pathway is an append-only journey engine built with Python, FastAPI, and SQLite. This guide walks you through installation, initializing a database, and exploring your first session.

## Installation

Install from PyPI:

```bash
pip install mcpt-pathway
```

Or install in development mode from source:

```bash
git clone https://github.com/mcp-tool-shop-org/pathway.git
cd pathway
pip install -e ".[dev]"
```

## Initialize the database

Create a fresh SQLite database:

```bash
python -m pathway.cli init
```

This creates a local `pathway.db` file with the events table and indexes.

## Import a sample session

Load the included sample session to explore the data model:

```bash
python -m pathway.cli import sample_session.jsonl
```

The JSONL file contains a sequence of events that demonstrate the full journey lifecycle — intent creation, waypoint navigation, backtracking, learning, and artifact production.

## View derived state

Query the computed views for any session:

```bash
python -m pathway.cli state sess_001
```

This returns three derived views computed from the raw event stream:

- **JourneyView** — current position, branches, visited waypoints
- **LearnedView** — preferences, concepts, and constraints with confidence scores
- **ArtifactView** — all outputs with supersedence tracking

## Start the API server

Launch the REST API for programmatic access:

```bash
python -m pathway.cli serve
```

The server starts on `localhost:8000` by default. See the [API Reference](/pathway/handbook/reference/) for endpoint details.

## Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PATHWAY_API_KEY` | Protect write endpoints with a bearer token | _(none — open)_ |
| `PATHWAY_MAX_PAYLOAD_SIZE` | Maximum request body size | `1048576` (1 MB) |
