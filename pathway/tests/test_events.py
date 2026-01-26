"""Tests for event models."""

import pytest
from datetime import datetime, timezone

from pathway.models.events import (
    EventEnvelope,
    EventType,
    Actor,
    ActorKind,
    IntentCreatedPayload,
    TrailVersionCreatedPayload,
    WaypointEnteredPayload,
    ChoiceMadePayload,
    StepCompletedPayload,
    BlockedPayload,
    BacktrackedPayload,
    ReplacedPayload,
    MergedPayload,
    ArtifactCreatedPayload,
    ArtifactSupersededPayload,
    PreferenceLearnedPayload,
    ConceptLearnedPayload,
    ConstraintLearnedPayload,
    Waypoint,
    Edge,
    WaypointKind,
    Artifact,
    ArtifactType,
)


def test_event_envelope_basic():
    """Test basic EventEnvelope creation."""
    event = EventEnvelope(
        event_id="e001",
        session_id="sess_001",
        seq=0,
        ts=datetime.now(timezone.utc),
        type=EventType.INTENT_CREATED,
        actor=Actor(kind=ActorKind.USER),
        payload={"goal": "Test goal"},
    )
    assert event.event_id == "e001"
    assert event.head_id == "main"  # default


def test_intent_created_payload():
    """Test IntentCreated payload parsing."""
    payload = IntentCreatedPayload(
        goal="Build a tool",
        motivation="Learn software",
        comfort_level="guide_me_closely",
    )
    assert payload.goal == "Build a tool"
    assert payload.comfort_level == "guide_me_closely"


def test_trail_version_created_payload():
    """Test TrailVersionCreated payload with waypoints and edges."""
    payload = TrailVersionCreatedPayload(
        trail_version_id="trail_v1",
        waypoints=[
            Waypoint(id="w0", title="Start", kind=WaypointKind.CHECKPOINT),
            Waypoint(id="w1", title="Do thing", kind=WaypointKind.ACTION),
        ],
        edges=[
            Edge(**{"from": "w0", "to": "w1", "label": "next"}),
        ],
    )
    assert len(payload.waypoints) == 2
    assert payload.edges[0].from_ == "w0"


def test_artifact_created_payload():
    """Test ArtifactCreated payload."""
    payload = ArtifactCreatedPayload(
        artifact=Artifact(
            artifact_id="a001",
            type=ArtifactType.CODE,
            content_ref="blob://test.py",
        )
    )
    assert payload.artifact.artifact_id == "a001"
    assert payload.artifact.reversible is True  # default


def test_preference_learned_payload_bounds():
    """Test PreferenceLearned confidence_delta bounds."""
    # Valid delta
    payload = PreferenceLearnedPayload(
        preference_id="pace.step_size",
        value="small",
        confidence_delta=0.5,
    )
    assert payload.confidence_delta == 0.5

    # Invalid delta (too high)
    with pytest.raises(ValueError):
        PreferenceLearnedPayload(
            preference_id="pace.step_size",
            value="small",
            confidence_delta=1.5,
        )


def test_event_get_payload_model():
    """Test EventEnvelope.get_payload_model()."""
    event = EventEnvelope(
        event_id="e001",
        session_id="sess_001",
        seq=0,
        ts=datetime.now(timezone.utc),
        type=EventType.INTENT_CREATED,
        actor=Actor(kind=ActorKind.USER),
        payload={"goal": "Test", "comfort_level": "guide_me_closely"},
    )

    model = event.get_payload_model()
    assert isinstance(model, IntentCreatedPayload)
    assert model.goal == "Test"


def test_blocked_payload():
    """Test Blocked payload with suggestions."""
    payload = BlockedPayload(
        waypoint_id="w1",
        summary="Got stuck",
        category="tooling",
        retryable=True,
        suggested_next=[
            {"kind": "backtrack_one", "detail": "Try again"},
        ],
    )
    assert payload.summary == "Got stuck"
    assert len(payload.suggested_next) == 1


def test_backtracked_payload():
    """Test Backtracked payload."""
    payload = BacktrackedPayload(
        from_event_id="e010",
        to_event_id="e005",
        mode="jump",
    )
    assert payload.keep_artifacts == "all"  # default


def test_merged_payload():
    """Test Merged payload."""
    payload = MergedPayload(
        merged_from_heads=["main", "b1"],
        merged_from_event_ids=["e010", "e020"],
        merge_waypoint_id="w5",
        result_head_id="main",
    )
    assert len(payload.merged_from_heads) == 2
