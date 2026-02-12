# Pathway Core v0.1.0 — Press Release

**FOR IMMEDIATE RELEASE**

## Pathway Core: An Append-Only Journey Engine Where Undo Never Erases Learning

*A new open-source primitive for building systems that respect human agency*

---

### What is Pathway?

Pathway Core is an append-only, learning-aware journey engine. It tracks where you've been, what you've learned, and what you've made—without ever rewriting history.

When you undo in Pathway, you don't destroy what happened. You navigate backward. The original path remains visible. The lessons remain learned.

**Undo is navigation. Learning persists.**

### Why does this matter?

Traditional systems treat undo as erasure. Hit Ctrl+Z and your work vanishes. Abandon a path and everything you learned disappears with it.

This is a lie about what happened.

Pathway tells the truth:
- Failed attempts remain visible
- Knowledge gained on dead ends persists
- Every decision has a history you can audit

This makes Pathway fundamentally honest infrastructure for learning systems, decision tracking, and human-AI collaboration.

### Technical Highlights

- **14 event types** covering the full journey lifecycle
- **SQLite storage** with thread-safe concurrent writes
- **Atomic sequence assignment** — no race conditions
- **Three derived views**: Journey (where you are), Learned (what you know), Artifacts (what you made)
- **FastAPI endpoints** with security baseline (API key, payload limits, input validation)
- **73 passing tests** covering core invariants

### Design Philosophy

Pathway does not decide for you. It does not hide your mistakes. It does not pretend to be smart.

It simply records what happened—honestly, immutably, inspectably—and lets you derive meaning from that truth.

### Get Started

```bash
git clone https://github.com/mcp-tool-shop-org/pathway
cd pathway
pip install -e ".[dev]"
python -m pathway.cli init
python -m pathway.cli import sample_session.jsonl
python -m pathway.cli state sess_001
```

### Links

- **Repository**: https://github.com/mcp-tool-shop-org/pathway
- **Documentation**: See README.md and WHY.md
- **License**: MIT

### The Bet

The bet is that systems which respect human agency—which show you the truth about where you are—will ultimately be more useful than systems which hide complexity to seem helpful.

Pathway Core v0.1.0 is infrastructure for that bet.

---

**Contact**: Open an issue at https://github.com/mcp-tool-shop-org/pathway/issues

**Release Date**: January 26, 2026

**Version**: 0.1.0
