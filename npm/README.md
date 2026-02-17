# @mcptoolshop/pathway

[![npm](https://img.shields.io/npm/v/@mcptoolshop/pathway)](https://www.npmjs.com/package/@mcptoolshop/pathway)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/mcp-tool-shop-org/pathway/blob/main/LICENSE)

**npm wrapper for [Pathway Core](https://github.com/mcp-tool-shop-org/pathway) — an append-only journey engine where undo never erases learning.**

## Install

```bash
npm install @mcptoolshop/pathway
```

This package provides a CLI wrapper that installs and delegates to the Python `pathway-core` package.

## Usage

```bash
npx @mcptoolshop/pathway init
npx @mcptoolshop/pathway import sample_session.jsonl
npx @mcptoolshop/pathway state sess_001
npx @mcptoolshop/pathway serve
```

## What is Pathway?

Traditional undo rewrites history. Pathway doesn't.

When you backtrack in Pathway, you create a new event pointing backward — the original path remains. When you learn something on a failed path, that knowledge persists. Your mistakes teach you; they don't disappear.

### Features

- **Append-only event log**: Events are never edited or deleted
- **Undo = pointer move**: Backtracking creates a new event and moves head
- **Learning persists**: Knowledge survives across backtracking and branches
- **Branching is first-class**: Git-like implicit divergence on new work after backtrack

## Requirements

- Node.js >= 18
- Python 3.10+ (installed automatically via postinstall if needed)

## Links

- [GitHub Repository](https://github.com/mcp-tool-shop-org/pathway)
- [PyPI Package](https://pypi.org/project/pathway-core/)

## License

MIT
