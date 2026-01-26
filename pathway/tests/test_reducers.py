"""Tests for reducers."""

import pytest
from datetime import datetime, timezone, timedelta

from pathway.models.events import (
    EventEnvelope,
    EventType,
    Actor,
    ActorKind,
    EvidenceRef,
)
from pathway.reducers.journey import reduce_journey
from pathway.reducers.learned import reduce_learned, clamp
from pathway.reducers.artifacts import reduce_artifacts, get_artifact_chain
from pathway.reducers.session import reduce_session_state


def make_event(
    event_id: str,
    event_type: EventType,
    seq: int,
    payload: dict,
    head_id: str = "main",
    waypoint_id: str | None = None,
    trail_version_id: str | None = None,
) -> EventEnvelope:
    """Helper to create test events."""
    return EventEnvelope(
        event_id=event_id,
        session_id="test",
        seq=seq,
        ts=datetime.now(timezone.utc) + timedelta(seconds=seq),
        type=event_type,
        head_id=head_id,
        waypoint_id=waypoint_id,
        trail_version_id=trail_version_id,
        actor=Actor(kind=ActorKind.SYSTEM),
        payload=payload,
    )


class TestJourneyReducer:
    """Tests for the journey reducer."""

    def test_empty_events(self):
        """Test with no events."""
        view = reduce_journey([])
        assert view.head_event_id is None
        assert view.current_waypoint_id is None

    def test_waypoint_tracking(self):
        """Test that waypoints are tracked correctly."""
        events = [
            make_event("e1", EventType.WAYPOINT_ENTERED, 0, {"waypoint_id": "w0", "via": "next"}, waypoint_id="w0"),
            make_event("e2", EventType.WAYPOINT_ENTERED, 1, {"waypoint_id": "w1", "via": "next"}, waypoint_id="w1"),
        ]
        view = reduce_journey(events)

        assert view.current_waypoint_id == "w1"
        assert len(view.visited_waypoints) == 2
        assert view.visited_waypoints[0].waypoint_id == "w0"
        assert view.visited_waypoints[1].waypoint_id == "w1"

    def test_branch_tips(self):
        """Test that branch tips are tracked."""
        events = [
            make_event("e1", EventType.WAYPOINT_ENTERED, 0, {"waypoint_id": "w0"}, head_id="main", waypoint_id="w0"),
            make_event("e2", EventType.WAYPOINT_ENTERED, 1, {"waypoint_id": "w1"}, head_id="b1", waypoint_id="w1"),
        ]
        view = reduce_journey(events)

        assert "main" in view.branch_tips
        assert "b1" in view.branch_tips
        assert view.branch_tips["main"].event_id == "e1"
        assert view.branch_tips["b1"].event_id == "e2"

    def test_active_head(self):
        """Test active head determination."""
        events = [
            make_event("e1", EventType.WAYPOINT_ENTERED, 0, {"waypoint_id": "w0"}, head_id="main"),
            make_event("e2", EventType.WAYPOINT_ENTERED, 1, {"waypoint_id": "w1"}, head_id="b1"),
            make_event("e3", EventType.WAYPOINT_ENTERED, 2, {"waypoint_id": "w2"}, head_id="main"),
        ]
        view = reduce_journey(events)

        # Active head is head of last event by seq
        assert view.active_head_id == "main"

    def test_backtrack_targets(self):
        """Test that backtrack targets exclude backtrack entries."""
        events = [
            make_event("e1", EventType.WAYPOINT_ENTERED, 0, {"waypoint_id": "w0", "via": "next"}),
            make_event("e2", EventType.WAYPOINT_ENTERED, 1, {"waypoint_id": "w1", "via": "next"}),
            make_event("e3", EventType.WAYPOINT_ENTERED, 2, {"waypoint_id": "w0", "via": "backtrack"}),
        ]
        view = reduce_journey(events)

        # e3 should not be a backtrack target (it's a backtrack itself)
        assert "e1" in view.backtrack_targets
        assert "e2" in view.backtrack_targets
        assert "e3" not in view.backtrack_targets


class TestLearnedReducer:
    """Tests for the learned reducer."""

    def test_clamp_function(self):
        """Test confidence clamping."""
        assert clamp(0.5) == 0.5
        assert clamp(-0.5) == 0.0
        assert clamp(1.5) == 1.0

    def test_empty_events(self):
        """Test with no events."""
        view = reduce_learned([])
        assert len(view.preferences) == 0
        assert len(view.concepts) == 0
        assert len(view.constraints) == 0

    def test_preference_learning(self):
        """Test preference accumulation."""
        events = [
            make_event("e1", EventType.PREFERENCE_LEARNED, 0, {
                "preference_id": "pace.step_size",
                "value": "small",
                "confidence_delta": 0.5,
            }),
            make_event("e2", EventType.PREFERENCE_LEARNED, 1, {
                "preference_id": "pace.step_size",
                "value": "small",
                "confidence_delta": 0.3,
            }),
        ]
        view = reduce_learned(events)

        assert "pace.step_size" in view.preferences
        assert view.preferences["pace.step_size"].confidence == 0.8  # 0.5 + 0.3
        assert view.preferences["pace.step_size"].value == "small"

    def test_concept_learning_with_evidence(self):
        """Test concept learning with evidence accumulation."""
        events = [
            make_event("e1", EventType.CONCEPT_LEARNED, 0, {
                "concept_id": "concept.input_output",
                "confidence_delta": 0.3,
                "evidence": [{"kind": "artifact", "id": "a1", "note": "test"}],
            }),
            make_event("e2", EventType.CONCEPT_LEARNED, 1, {
                "concept_id": "concept.input_output",
                "confidence_delta": 0.2,
                "evidence": [{"kind": "artifact", "id": "a2"}],
            }),
        ]
        view = reduce_learned(events)

        assert view.concepts["concept.input_output"].confidence == 0.5
        assert len(view.concepts["concept.input_output"].evidence) == 2

    def test_confidence_clamps_to_one(self):
        """Test that confidence clamps to 1.0."""
        events = [
            make_event("e1", EventType.CONCEPT_LEARNED, 0, {
                "concept_id": "concept.test",
                "confidence_delta": 0.9,
            }),
            make_event("e2", EventType.CONCEPT_LEARNED, 1, {
                "concept_id": "concept.test",
                "confidence_delta": 0.5,  # Would go to 1.4
            }),
        ]
        view = reduce_learned(events)

        assert view.concepts["concept.test"].confidence == 1.0

    def test_constraint_learning(self):
        """Test constraint recording."""
        events = [
            make_event("e1", EventType.CONSTRAINT_LEARNED, 0, {
                "constraint_id": "environment.os",
                "value": "windows",
                "confidence_delta": 1.0,
            }),
        ]
        view = reduce_learned(events)

        assert view.constraints["environment.os"].value == "windows"
        assert view.constraints["environment.os"].confidence == 1.0


class TestArtifactsReducer:
    """Tests for the artifacts reducer."""

    def test_empty_events(self):
        """Test with no events."""
        view = reduce_artifacts([])
        assert len(view.artifacts) == 0

    def test_artifact_creation(self):
        """Test artifact creation tracking."""
        events = [
            make_event("e1", EventType.ARTIFACT_CREATED, 0, {
                "artifact": {
                    "artifact_id": "a1",
                    "type": "code",
                    "content_ref": "blob://test.py",
                    "produced_at_waypoint_id": "w1",
                },
            }, waypoint_id="w1"),
        ]
        view = reduce_artifacts(events)

        assert "a1" in view.artifacts
        assert view.artifacts["a1"].is_active
        assert view.artifacts["a1"].produced_by_event_id == "e1"

    def test_artifact_supersedence(self):
        """Test artifact supersedence."""
        events = [
            make_event("e1", EventType.ARTIFACT_CREATED, 0, {
                "artifact": {
                    "artifact_id": "a1",
                    "type": "code",
                    "content_ref": "blob://v1.py",
                },
            }),
            make_event("e2", EventType.ARTIFACT_CREATED, 1, {
                "artifact": {
                    "artifact_id": "a2",
                    "type": "code",
                    "content_ref": "blob://v2.py",
                },
            }),
            make_event("e3", EventType.ARTIFACT_SUPERSEDED, 2, {
                "artifact_id": "a1",
                "superseded_by_artifact_id": "a2",
            }),
        ]
        view = reduce_artifacts(events)

        assert not view.artifacts["a1"].is_active
        assert view.artifacts["a1"].superseded_by == "a2"
        assert view.artifacts["a2"].is_active

    def test_active_artifacts_property(self):
        """Test active_artifacts property."""
        events = [
            make_event("e1", EventType.ARTIFACT_CREATED, 0, {
                "artifact": {"artifact_id": "a1", "type": "code", "content_ref": "x"},
            }),
            make_event("e2", EventType.ARTIFACT_CREATED, 1, {
                "artifact": {"artifact_id": "a2", "type": "code", "content_ref": "y"},
            }),
            make_event("e3", EventType.ARTIFACT_SUPERSEDED, 2, {
                "artifact_id": "a1",
                "superseded_by_artifact_id": "a2",
            }),
        ]
        view = reduce_artifacts(events)

        assert len(view.active_artifacts) == 1
        assert "a2" in view.active_artifacts

    def test_artifact_chain(self):
        """Test get_artifact_chain helper."""
        events = [
            make_event("e1", EventType.ARTIFACT_CREATED, 0, {
                "artifact": {"artifact_id": "a1", "type": "code", "content_ref": "x"},
            }),
            make_event("e2", EventType.ARTIFACT_CREATED, 1, {
                "artifact": {"artifact_id": "a2", "type": "code", "content_ref": "y"},
            }),
            make_event("e3", EventType.ARTIFACT_SUPERSEDED, 2, {
                "artifact_id": "a1",
                "superseded_by_artifact_id": "a2",
            }),
            make_event("e4", EventType.ARTIFACT_CREATED, 3, {
                "artifact": {"artifact_id": "a3", "type": "code", "content_ref": "z"},
            }),
            make_event("e5", EventType.ARTIFACT_SUPERSEDED, 4, {
                "artifact_id": "a2",
                "superseded_by_artifact_id": "a3",
            }),
        ]
        view = reduce_artifacts(events)
        chain = get_artifact_chain(view, "a3")

        assert chain == ["a1", "a2", "a3"]


class TestSessionReducer:
    """Tests for the combined session reducer."""

    def test_full_session_state(self):
        """Test computing full session state."""
        events = [
            make_event("e1", EventType.WAYPOINT_ENTERED, 0, {"waypoint_id": "w0", "via": "next"}, waypoint_id="w0"),
            make_event("e2", EventType.CONCEPT_LEARNED, 1, {
                "concept_id": "concept.test",
                "confidence_delta": 0.5,
            }),
            make_event("e3", EventType.ARTIFACT_CREATED, 2, {
                "artifact": {"artifact_id": "a1", "type": "code", "content_ref": "x"},
            }),
        ]

        state = reduce_session_state("test", events)

        assert state.session_id == "test"
        assert state.event_count == 3
        assert state.journey.current_waypoint_id == "w0"
        assert state.learned.concepts["concept.test"].confidence == 0.5
        assert "a1" in state.artifacts.artifacts
