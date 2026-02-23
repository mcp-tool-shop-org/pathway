# Pathway Core

An append-only journey engine where undo never erases learning.

## Key Features

- **Append-Only Event Log** — Events are never edited or deleted
- **Undo = Pointer Move** — Backtracking creates a new event, original path remains
- **Learning Persists** — Knowledge survives across backtracking and branches
- **First-Class Branching** — Git-like implicit divergence on new work after backtrack
- **14 Event Types** — Full journey lifecycle coverage
- **3 Derived Views** — JourneyView, LearnedView, ArtifactView

## Install / Quick Start

```bash
pip install pathway-core
python -m pathway.cli init
python -m pathway.cli serve
```

## Links

- [GitHub Repository](https://github.com/mcp-tool-shop-org/pathway)
- [pathway-core on PyPI](https://pypi.org/project/pathway-core/)
- [MCP Tool Shop](https://github.com/mcp-tool-shop-org)
