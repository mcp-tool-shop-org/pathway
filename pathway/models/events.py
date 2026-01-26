"""Event models for Pathway's append-only event store.

All events share a common envelope with causal links for undo/branching.
The 14 event types cover the complete lifecycle of a learning journey.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class EventType(str, Enum):
    """All event types in Pathway."""

    INTENT_CREATED = "IntentCreated"
    TRAIL_VERSION_CREATED = "TrailVersionCreated"
    WAYPOINT_ENTERED = "WaypointEntered"
    CHOICE_MADE = "ChoiceMade"
    STEP_COMPLETED = "StepCompleted"
    BLOCKED = "Blocked"
    BACKTRACKED = "Backtracked"
    REPLANNED = "Replanned"
    MERGED = "Merged"
    ARTIFACT_CREATED = "ArtifactCreated"
    ARTIFACT_SUPERSEDED = "ArtifactSuperseded"
    PREFERENCE_LEARNED = "PreferenceLearned"
    CONCEPT_LEARNED = "ConceptLearned"
    CONSTRAINT_LEARNED = "ConstraintLearned"


class ActorKind(str, Enum):
    """Who or what created the event."""

    USER = "user"
    SYSTEM = "system"


class WaypointKind(str, Enum):
    """Types of waypoints in a trail."""

    CHECKPOINT = "checkpoint"
    ACTION = "action"
    BRANCH = "branch"
    MILESTONE = "milestone"


class BlockCategory(str, Enum):
    """Categories of blockers."""

    CONFUSION = "confusion"
    TOOLING = "tooling"
    RUNTIME_ERROR = "runtime_error"
    MISSING_INFO = "missing_info"
    EXTERNAL_DEPENDENCY = "external_dependency"


class SuggestedNextKind(str, Enum):
    """Types of suggested next actions when blocked."""

    BACKTRACK_ONE = "backtrack_one"
    SWITCH_PATH = "switch_path"
    ASK_QUESTION = "ask_question"
    SIMPLIFY = "simplify"
    REPLAN = "replan"


class BacktrackMode(str, Enum):
    """How far back to go."""

    ONE_STEP = "one_step"
    JUMP = "jump"


class ArtifactType(str, Enum):
    """Types of artifacts produced during the journey."""

    CODE = "code"
    DOC = "doc"
    CONFIG = "config"
    RUN_LOG = "run_log"
    SCREENSHOT = "screenshot"
    OTHER = "other"


class SideEffects(str, Enum):
    """Side effects of an artifact."""

    NONE = "none"
    LOCAL = "local"
    REMOTE = "remote"


# -----------------------------------------------------------------------------
# Common types
# -----------------------------------------------------------------------------


class Actor(BaseModel):
    """Who created the event."""

    kind: ActorKind
    id: str | None = None


class EvidenceRef(BaseModel):
    """Reference to evidence supporting a learned update."""

    kind: Literal["artifact", "event"]
    id: str
    note: str | None = None


# -----------------------------------------------------------------------------
# Payload types for each event
# -----------------------------------------------------------------------------


class IntentCreatedPayload(BaseModel):
    """Payload for IntentCreated event."""

    goal: str
    motivation: str | None = None
    starting_point: str | None = None
    constraints: list[dict[str, str]] | None = None
    comfort_level: Literal[
        "guide_me_closely", "explain_as_we_go", "let_me_explore"
    ] | None = None


class Waypoint(BaseModel):
    """A waypoint in a trail."""

    id: str
    title: str
    kind: WaypointKind


class EdgeOption(BaseModel):
    """An option at a branch point."""

    option_id: str
    title: str
    to: str
    effort: Literal["low", "medium", "high"] | None = None
    reversibility: Literal["easy", "partial", "hard"] | None = None


class Edge(BaseModel):
    """An edge connecting waypoints."""

    model_config = {"populate_by_name": True}

    from_: str = Field(alias="from")
    to: str
    label: Literal["next", "options"]
    options: list[EdgeOption] | None = None


class TrailVersionCreatedPayload(BaseModel):
    """Payload for TrailVersionCreated event."""

    trail_version_id: str
    reason: str | None = None
    waypoints: list[Waypoint]
    edges: list[Edge]


class WaypointEnteredPayload(BaseModel):
    """Payload for WaypointEntered event."""

    waypoint_id: str
    via: Literal["next", "jump", "backtrack", "replan", "merge"] | None = None
    from_waypoint_id: str | None = None


class ChoiceReason(BaseModel):
    """A reason for making a choice."""

    kind: Literal[
        "matches_preference",
        "low_friction",
        "fits_constraints",
        "teaches_goal",
        "unblocks",
    ]
    detail: str | None = None


class ChoiceRationale(BaseModel):
    """Why a choice was made."""

    suggested_by: Literal["system", "user"] | None = None
    reasons: list[ChoiceReason] | None = None


class ChoiceMadePayload(BaseModel):
    """Payload for ChoiceMade event."""

    from_waypoint_id: str
    option_id: str
    to_waypoint_id: str
    rationale: ChoiceRationale | None = None


class StepCompletedPayload(BaseModel):
    """Payload for StepCompleted event."""

    waypoint_id: str
    outcome: Literal["ok", "ok_with_notes"]
    notes: str | None = None
    evidence: list[EvidenceRef] | None = None


class SuggestedNext(BaseModel):
    """A suggested next action when blocked."""

    kind: SuggestedNextKind
    detail: str | None = None


class BlockedPayload(BaseModel):
    """Payload for Blocked event."""

    waypoint_id: str
    summary: str
    category: BlockCategory | None = None
    retryable: bool
    suggested_next: list[SuggestedNext] | None = None
    evidence: list[EvidenceRef] | None = None


class BacktrackedPayload(BaseModel):
    """Payload for Backtracked event."""

    from_event_id: str
    to_event_id: str
    mode: BacktrackMode
    keep_artifacts: Literal["all"] = "all"
    note: str | None = None


class LearnedRef(BaseModel):
    """Reference to a learned item."""

    kind: Literal["preference", "concept", "constraint"]
    id: str


class ReplanBasedOn(BaseModel):
    """What triggered the replan."""

    learned_refs: list[LearnedRef] | None = None
    triggering_event_id: str | None = None


class ReplacedPayload(BaseModel):
    """Payload for Replanned event."""

    from_trail_version_id: str
    to_trail_version_id: str
    reason: str
    based_on: ReplanBasedOn | None = None


class MergedPayload(BaseModel):
    """Payload for Merged event."""

    merged_from_heads: list[str]
    merged_from_event_ids: list[str]
    merge_waypoint_id: str
    result_head_id: str
    notes: str | None = None


class Artifact(BaseModel):
    """An artifact produced during the journey."""

    artifact_id: str
    type: ArtifactType
    title: str | None = None
    content_ref: str
    produced_at_waypoint_id: str | None = None
    reversible: bool = True
    side_effects: SideEffects = SideEffects.NONE


class ArtifactCreatedPayload(BaseModel):
    """Payload for ArtifactCreated event."""

    artifact: Artifact


class ArtifactSupersededPayload(BaseModel):
    """Payload for ArtifactSuperseded event."""

    artifact_id: str
    superseded_by_artifact_id: str
    reason: str | None = None


class PreferenceLearnedPayload(BaseModel):
    """Payload for PreferenceLearned event."""

    preference_id: str  # PreferenceId value
    value: str | int | bool
    confidence_delta: float = Field(ge=-1.0, le=1.0)
    evidence: list[EvidenceRef] | None = None
    note: str | None = None


class ConceptLearnedPayload(BaseModel):
    """Payload for ConceptLearned event."""

    concept_id: str  # ConceptId value
    confidence_delta: float = Field(ge=-1.0, le=1.0)
    evidence: list[EvidenceRef] | None = None
    note: str | None = None


class ConstraintLearnedPayload(BaseModel):
    """Payload for ConstraintLearned event."""

    constraint_id: str  # ConstraintId value
    value: str | int | bool
    confidence_delta: float = Field(ge=-1.0, le=1.0)
    evidence: list[EvidenceRef] | None = None
    note: str | None = None


# -----------------------------------------------------------------------------
# Event envelope
# -----------------------------------------------------------------------------


class EventEnvelope(BaseModel):
    """The common envelope for all Pathway events.

    Events are append-only and form a DAG via parent_event_id.
    The head_id identifies which branch an event belongs to.
    """

    event_id: str
    session_id: str
    seq: int = Field(ge=0)
    ts: datetime
    type: EventType

    # Causal links
    parent_event_id: str | None = None
    head_id: str = "main"

    # Context references
    trail_version_id: str | None = None
    waypoint_id: str | None = None

    # Who created it
    actor: Actor

    # Event-specific data
    payload: dict[str, Any]

    def get_payload_model(self) -> BaseModel | None:
        """Parse payload into the appropriate typed model."""
        payload_types: dict[EventType, type[BaseModel]] = {
            EventType.INTENT_CREATED: IntentCreatedPayload,
            EventType.TRAIL_VERSION_CREATED: TrailVersionCreatedPayload,
            EventType.WAYPOINT_ENTERED: WaypointEnteredPayload,
            EventType.CHOICE_MADE: ChoiceMadePayload,
            EventType.STEP_COMPLETED: StepCompletedPayload,
            EventType.BLOCKED: BlockedPayload,
            EventType.BACKTRACKED: BacktrackedPayload,
            EventType.REPLANNED: ReplacedPayload,
            EventType.MERGED: MergedPayload,
            EventType.ARTIFACT_CREATED: ArtifactCreatedPayload,
            EventType.ARTIFACT_SUPERSEDED: ArtifactSupersededPayload,
            EventType.PREFERENCE_LEARNED: PreferenceLearnedPayload,
            EventType.CONCEPT_LEARNED: ConceptLearnedPayload,
            EventType.CONSTRAINT_LEARNED: ConstraintLearnedPayload,
        }
        model_cls = payload_types.get(self.type)
        if model_cls:
            return model_cls.model_validate(self.payload)
        return None
