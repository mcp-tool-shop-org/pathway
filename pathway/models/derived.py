"""Derived view models computed from the event log.

These are the read-side projections that the UI consumes:
- JourneyView: Where the user is in their journey
- LearnedView: What the system has learned about the user
- ArtifactView: What outputs have been produced
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from pathway.models.events import ArtifactType, EvidenceRef, SideEffects


# -----------------------------------------------------------------------------
# Journey View
# -----------------------------------------------------------------------------


class VisitedWaypoint(BaseModel):
    """A waypoint the user has visited."""

    waypoint_id: str
    timestamp: datetime
    event_id: str


class BranchTip(BaseModel):
    """The tip of a branch in the journey DAG."""

    head_id: str
    event_id: str
    waypoint_id: str | None
    seq: int


class JourneyView(BaseModel):
    """The current state of the user's journey through the trail.

    Computed by reducing all events in a session.
    """

    # Current position
    head_event_id: str | None = None
    current_waypoint_id: str | None = None
    active_head_id: str = "main"

    # Active trail
    active_trail_version_id: str | None = None

    # Branch state
    branch_tips: dict[str, BranchTip] = {}

    # History
    visited_waypoints: list[VisitedWaypoint] = []

    # Valid backtrack targets (event_ids user can jump back to)
    backtrack_targets: list[str] = []


# -----------------------------------------------------------------------------
# Learned View
# -----------------------------------------------------------------------------


class LearnedRecord(BaseModel):
    """A single learned item with confidence and evidence.

    Confidence is a float in [0.0, 1.0].
    Evidence refs link to artifacts or events that support the learning.
    """

    id: str
    value: Any | None = None  # For preferences and constraints
    confidence: float = 0.0
    evidence: list[EvidenceRef] = []
    updated_at_seq: int = 0


class LearnedView(BaseModel):
    """Aggregated learned state about the user.

    Built from PreferenceLearned, ConceptLearned, and ConstraintLearned events.
    Learning persists across backtracking - it's never erased.
    """

    preferences: dict[str, LearnedRecord] = {}
    constraints: dict[str, LearnedRecord] = {}
    concepts: dict[str, LearnedRecord] = {}


# -----------------------------------------------------------------------------
# Artifact View
# -----------------------------------------------------------------------------


class ArtifactRecord(BaseModel):
    """A single artifact with its metadata."""

    artifact_id: str
    type: ArtifactType
    title: str | None = None
    content_ref: str
    produced_at_waypoint_id: str | None = None
    produced_by_event_id: str
    produced_at_seq: int
    reversible: bool = True
    side_effects: SideEffects = SideEffects.NONE

    # Supersedence tracking
    superseded_by: str | None = None
    is_active: bool = True


class ArtifactView(BaseModel):
    """All artifacts produced during the journey.

    An artifact is active unless it has been superseded.
    Artifacts are never deleted, only superseded.
    """

    artifacts: dict[str, ArtifactRecord] = {}

    @property
    def active_artifacts(self) -> dict[str, ArtifactRecord]:
        """Get only the active (non-superseded) artifacts."""
        return {k: v for k, v in self.artifacts.items() if v.is_active}

    @property
    def superseded_artifacts(self) -> dict[str, ArtifactRecord]:
        """Get only the superseded artifacts."""
        return {k: v for k, v in self.artifacts.items() if not v.is_active}


# -----------------------------------------------------------------------------
# Combined Session State
# -----------------------------------------------------------------------------


class SessionState(BaseModel):
    """Complete derived state for a session.

    This is what the API returns and what the UI consumes.
    """

    session_id: str
    journey: JourneyView
    learned: LearnedView
    artifacts: ArtifactView

    # Metadata
    event_count: int = 0
    last_event_seq: int = -1
    last_event_ts: datetime | None = None
