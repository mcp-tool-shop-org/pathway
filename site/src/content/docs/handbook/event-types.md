---
title: Event Types
description: All 14 event types in the Pathway journey lifecycle.
sidebar:
  order: 3
---

Pathway uses 14 event types to model the complete journey lifecycle. Every action — from setting a goal to learning a constraint — is captured as an immutable event in the append-only log.

## Event type reference

| Type | Purpose |
|------|---------|
| `IntentCreated` | Records the user's goal and context at the start of a journey |
| `TrailVersionCreated` | Defines or revises the learning path/map |
| `WaypointEntered` | Marks navigation to a specific point on the trail |
| `ChoiceMade` | Records a branching decision by the user |
| `StepCompleted` | Marks successful completion of a waypoint |
| `Blocked` | Records friction — the user hit an obstacle |
| `Backtracked` | The user went back (undo as navigation) |
| `Replanned` | The trail was revised based on new information |
| `Merged` | Two branches converge back together |
| `ArtifactCreated` | An output was produced (code, document, report) |
| `ArtifactSuperseded` | A previous artifact was replaced by a newer version |
| `PreferenceLearned` | How the user likes to learn (style, pace, format) |
| `ConceptLearned` | A concept the user now understands |
| `ConstraintLearned` | A fact about the user's environment or limitations |

## Journey events

**IntentCreated**, **TrailVersionCreated**, **WaypointEntered**, **ChoiceMade**, **StepCompleted**, and **Blocked** model the forward motion of a journey. They describe what the user is trying to do, where they are, and what's in their way.

## Navigation events

**Backtracked**, **Replanned**, and **Merged** handle non-linear movement. Backtracking creates a new event rather than deleting history. Replanning revises the trail. Merging brings divergent branches back together.

## Artifact events

**ArtifactCreated** and **ArtifactSuperseded** track outputs. When an artifact is superseded, the original remains in the log — only the `ArtifactView` reflects the current version.

## Learning events

**PreferenceLearned**, **ConceptLearned**, and **ConstraintLearned** capture knowledge that persists across branches and backtracks. These events feed the `LearnedView` with confidence scores that accumulate over time.
