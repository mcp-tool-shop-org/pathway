---
title: Philosophy & Features
description: Why Pathway uses append-only events and what that enables.
sidebar:
  order: 2
---

Pathway is built on a single conviction: **undo should be navigation, not erasure.**

## Traditional undo rewrites history

Most systems treat undo as deletion. You go back, the forward state vanishes, and the system pretends it never happened. This is convenient but dishonest — it throws away information about what you tried and what you learned along the way.

## Pathway keeps everything

When you backtrack in Pathway, the engine creates a new `Backtracked` event pointing backward. The original forward path remains in the log, fully intact. Nothing is overwritten. Nothing is deleted.

This means:
- **Every event that happened is recorded.** There is no mechanism to pretend something didn't happen.
- **A failed attempt isn't wasted.** It becomes a preference learned, a concept understood, or a constraint discovered.
- **Going back doesn't delete the forward path.** It's a new event that says "I chose to revisit."

## Core features

### Append-only event log
Events are never edited or deleted. The full history is always preserved. This gives you a complete audit trail and enables time-travel queries across the entire journey.

### Undo = pointer move
Backtracking creates a new event and moves the head pointer — the original path remains intact. You can always see what happened before the backtrack.

### Learning persists
Knowledge survives across backtracking and branches. If you discover a preference on a path you later abandon, that preference is still in your `LearnedView`. Failed paths still teach.

### First-class branching
When new work happens after a backtrack, Pathway creates an implicit branch — similar to how Git handles detached HEAD commits. Branches can later be merged with the `Merged` event type.

### Derived views
Three computed views are built from the event stream in real time:

- **JourneyView** — current position, branches, visited waypoints
- **LearnedView** — preferences, concepts, constraints with confidence scores
- **ArtifactView** — all outputs with supersedence tracking

### FastAPI + SQLite
A REST API with built-in authentication, payload limits, and SQLite persistence ships out of the box. No external database required.
