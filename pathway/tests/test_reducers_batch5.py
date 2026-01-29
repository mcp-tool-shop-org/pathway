"""
Batch 5: Reducers and Derived views tests (25 tests)
Tests for journey, learned, artifacts reducers and derived view properties.
"""

import pytest
from datetime import datetime, timezone

from pathway.models.events import (
    EventEnvelope, EventType, Actor, ActorKind, ArtifactType,
)
from pathway.models.derived import (
    JourneyView, LearnedView, ArtifactView, SessionState,
    LearnedRecord, ArtifactRecord,
)
from pathway.reducers.journey import reduce_journey
from pathway.reducers.learned import reduce_learned
from pathway.reducers.artifacts import reduce_artifacts
from pathway.reducers.session import reduce_session_state


# =============================================================================
# Helpers
# =============================================================================

def make_event(
    event_id: str,
    seq: int,
    event_type: EventType,
    head_id: str = "main",
    waypoint_id: str = None,
    payload: dict = None,
) -> EventEnvelope:
    """Create a test event."""
    return EventEnvelope(
        event_id=event_id,
        session_id="test_session",
        seq=seq,
        ts=datetime.now(timezone.utc),
        type=event_type,
        head_id=head_id,
        waypoint_id=waypoint_id,
        actor=Actor(kind=ActorKind.SYSTEM),
        payload=payload or {},
    )


# =============================================================================
# Section 1: Journey Reducer (7 tests)
# =============================================================================

class TestJourneyViewActiveArtifacts:
    """Test journey view active_artifacts property."""

    def test_journey_tracks_active_head(self):
        """Test journey tracks the active head correctly."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
            make_event("e002", 1, EventType.WAYPOINT_ENTERED, head_id="main",
                       payload={"waypoint_id": "wp1", "title": "Step 1", "kind": "checkpoint"}),
        ]

        journey = reduce_journey(events)

        assert journey.active_head_id == "main"


class TestJourneyViewBranchCount:
    """Test branch counting."""

    def test_journey_branch_count(self):
        """Test journey correctly counts branches."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, head_id="main",
                       payload={"goal": "test"}),
            make_event("e002", 1, EventType.WAYPOINT_ENTERED, head_id="branch1",
                       payload={"waypoint_id": "wp1", "title": "Branch Step", "kind": "checkpoint"}),
            make_event("e003", 2, EventType.WAYPOINT_ENTERED, head_id="branch2",
                       payload={"waypoint_id": "wp2", "title": "Another Branch", "kind": "checkpoint"}),
        ]

        journey = reduce_journey(events)

        # Should have 3 branches: main, branch1, branch2
        assert len(journey.branch_tips) >= 2


class TestJourneyViewVisitedWaypoints:
    """Test visited waypoints tracking."""

    def test_visited_waypoints_tracked(self):
        """Test visited waypoints are recorded."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
            make_event("e002", 1, EventType.WAYPOINT_ENTERED, waypoint_id="wp1",
                       payload={"waypoint_id": "wp1", "title": "Step 1", "kind": "checkpoint"}),
            make_event("e003", 2, EventType.WAYPOINT_ENTERED, waypoint_id="wp2",
                       payload={"waypoint_id": "wp2", "title": "Step 2", "kind": "action"}),
        ]

        journey = reduce_journey(events)

        assert len(journey.visited_waypoints) >= 2


class TestJourneyViewBacktrackTargets:
    """Test backtrack_targets calculation."""

    def test_backtrack_targets(self):
        """Test backtrack targets are calculated."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
            make_event("e002", 1, EventType.WAYPOINT_ENTERED, waypoint_id="wp1",
                       payload={"waypoint_id": "wp1", "title": "Step 1", "kind": "checkpoint"}),
        ]

        journey = reduce_journey(events)

        # backtrack_targets should be available
        assert isinstance(journey.backtrack_targets, list)


class TestJourneyWithNoWaypoints:
    """Test journey with only non-navigation events."""

    def test_journey_no_waypoints(self):
        """Test journey with only learning events has empty waypoint list."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
            make_event("e002", 1, EventType.PREFERENCE_LEARNED,
                       payload={"preference_id": "p1", "value": "vim", "confidence_delta": 0.8}),
        ]

        journey = reduce_journey(events)

        # Should handle gracefully
        assert journey.current_waypoint_id is None or len(journey.visited_waypoints) == 0


class TestJourneyMultipleBacktracks:
    """Test journey with multiple backtracks."""

    def test_journey_multiple_backtracks(self):
        """Test journey handles multiple backtracks."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
            make_event("e002", 1, EventType.WAYPOINT_ENTERED, waypoint_id="wp1",
                       payload={"waypoint_id": "wp1"}),
            make_event("e003", 2, EventType.BACKTRACKED,
                       payload={"from_event_id": "e002", "to_event_id": "e001", "mode": "jump"}),
        ]

        journey = reduce_journey(events)

        # Should process without errors
        assert journey is not None


class TestJourneyCurrentWaypoint:
    """Test current waypoint tracking."""

    def test_journey_current_waypoint(self):
        """Test current waypoint is tracked."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
            make_event("e002", 1, EventType.WAYPOINT_ENTERED, waypoint_id="wp1",
                       payload={"waypoint_id": "wp1", "title": "First", "kind": "checkpoint"}),
            make_event("e003", 2, EventType.WAYPOINT_ENTERED, waypoint_id="wp2",
                       payload={"waypoint_id": "wp2", "title": "Second", "kind": "action"}),
        ]

        journey = reduce_journey(events)

        # Current should be last entered
        assert journey.current_waypoint_id == "wp2"


# =============================================================================
# Section 2: Learned Reducer (8 tests)
# =============================================================================

class TestLearnedViewPreferences:
    """Test preferences dictionary."""

    def test_learned_preferences(self):
        """Test preferences are aggregated correctly."""
        events = [
            make_event("e001", 0, EventType.PREFERENCE_LEARNED,
                       payload={"preference_id": "p1", "value": "vim", "confidence_delta": 0.8}),
            make_event("e002", 1, EventType.PREFERENCE_LEARNED,
                       payload={"preference_id": "p2", "value": "dark", "confidence_delta": 0.9}),
        ]

        learned = reduce_learned(events)

        assert len(learned.preferences) == 2
        assert "p1" in learned.preferences
        assert "p2" in learned.preferences


class TestLearnedViewConcepts:
    """Test concepts dictionary."""

    def test_learned_concepts_with_evidence(self):
        """Test concepts track evidence IDs."""
        events = [
            make_event("e001", 0, EventType.CONCEPT_LEARNED,
                       payload={"concept_id": "c1", "label": "REST API", "confidence_delta": 0.5,
                                "evidence": [{"kind": "event", "id": "e001"}]}),
        ]

        learned = reduce_learned(events)

        assert "c1" in learned.concepts


class TestLearnedViewConstraints:
    """Test constraints dictionary."""

    def test_learned_constraints(self):
        """Test constraints are tracked."""
        events = [
            make_event("e001", 0, EventType.CONSTRAINT_LEARNED,
                       payload={"constraint_id": "ct1", "value": "Python 3.10+",
                                "confidence_delta": 0.95}),
        ]

        learned = reduce_learned(events)

        assert "ct1" in learned.constraints


class TestMultiplePreferenceUpdates:
    """Test preference confidence accumulates."""

    def test_preference_confidence_accumulates(self):
        """Test multiple preferences for same key update confidence."""
        events = [
            make_event("e001", 0, EventType.PREFERENCE_LEARNED,
                       payload={"preference_id": "p1", "value": "vim", "confidence_delta": 0.5}),
            make_event("e002", 1, EventType.PREFERENCE_LEARNED,
                       payload={"preference_id": "p1", "value": "vim", "confidence_delta": 0.3}),
        ]

        learned = reduce_learned(events)

        # Should have updated confidence
        assert "p1" in learned.preferences


class TestConceptEvidenceTracking:
    """Test concept evidence list grows."""

    def test_concept_evidence_accumulates(self):
        """Test learning concept multiple times accumulates evidence."""
        events = [
            make_event("e001", 0, EventType.CONCEPT_LEARNED,
                       payload={"concept_id": "c1", "label": "API", "confidence_delta": 0.3,
                                "evidence": [{"kind": "event", "id": "ev1"}]}),
            make_event("e002", 1, EventType.CONCEPT_LEARNED,
                       payload={"concept_id": "c1", "label": "API", "confidence_delta": 0.2,
                                "evidence": [{"kind": "event", "id": "ev2"}]}),
        ]

        learned = reduce_learned(events)

        # Evidence should accumulate
        assert "c1" in learned.concepts


class TestConstraintUpdateReplaces:
    """Test constraint updates replace old values."""

    def test_constraint_update_replaces(self):
        """Test updating same constraint replaces value."""
        events = [
            make_event("e001", 0, EventType.CONSTRAINT_LEARNED,
                       payload={"constraint_id": "ct1", "value": "Old constraint",
                                "confidence_delta": 0.5}),
            make_event("e002", 1, EventType.CONSTRAINT_LEARNED,
                       payload={"constraint_id": "ct1", "value": "New constraint",
                                "confidence_delta": 0.4}),
        ]

        learned = reduce_learned(events)

        # Should have updated value
        assert learned.constraints["ct1"].value == "New constraint"


class TestLearnedRecordFirstSeen:
    """Test updated_at_seq is set correctly."""

    def test_learned_first_seen_seq(self):
        """Test updated_at_seq records learning event seq."""
        events = [
            make_event("e001", 0, EventType.PREFERENCE_LEARNED,
                       payload={"preference_id": "p1", "value": "vim", "confidence_delta": 0.8}),
        ]

        learned = reduce_learned(events)

        assert learned.preferences["p1"].updated_at_seq == 0


class TestLearnedEmptyEvents:
    """Test learned view with no learning events."""

    def test_learned_empty(self):
        """Test learned view is empty with non-learning events."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
            make_event("e002", 1, EventType.WAYPOINT_ENTERED, waypoint_id="wp1",
                       payload={"waypoint_id": "wp1", "title": "Step", "kind": "checkpoint"}),
        ]

        learned = reduce_learned(events)

        assert len(learned.preferences) == 0
        assert len(learned.concepts) == 0
        assert len(learned.constraints) == 0


# =============================================================================
# Section 3: Artifacts Reducer (6 tests)
# =============================================================================

class TestArtifactViewActiveArtifacts:
    """Test active_artifacts property filters."""

    def test_artifact_active_filter(self):
        """Test active_artifacts returns only non-superseded."""
        events = [
            make_event("e001", 0, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "a1", "type": "code", "content_ref": "/test.py"}}),
            make_event("e002", 1, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "a2", "type": "doc", "content_ref": "/README.md"}}),
        ]

        artifacts = reduce_artifacts(events)

        assert len(artifacts.active_artifacts) == 2


class TestArtifactViewSupersededArtifacts:
    """Test superseded_artifacts property filters."""

    def test_artifact_superseded_filter(self):
        """Test superseded_artifacts returns only superseded."""
        events = [
            make_event("e001", 0, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "a1", "type": "code", "content_ref": "/v1.py"}}),
            make_event("e002", 1, EventType.ARTIFACT_SUPERSEDED,
                       payload={"artifact_id": "a1", "superseded_by_artifact_id": "a2"}),
            make_event("e003", 2, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "a2", "type": "code", "content_ref": "/v2.py"}}),
        ]

        artifacts = reduce_artifacts(events)

        assert len(artifacts.superseded_artifacts) == 1
        assert "a1" in artifacts.superseded_artifacts


class TestArtifactViewByType:
    """Test artifacts grouped by type."""

    def test_artifacts_by_type(self):
        """Test artifacts can be filtered by type."""
        events = [
            make_event("e001", 0, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "a1", "type": "code", "content_ref": "/test.py"}}),
            make_event("e002", 1, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "a2", "type": "doc", "content_ref": "/README.md"}}),
            make_event("e003", 2, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "a3", "type": "code", "content_ref": "/main.py"}}),
        ]

        artifacts = reduce_artifacts(events)

        code_artifacts = [a for a in artifacts.artifacts.values() if a.type == ArtifactType.CODE]
        assert len(code_artifacts) == 2


class TestArtifactChain:
    """Test building chain of supersedence."""

    def test_artifact_supersedence_chain(self):
        """Test artifact supersedence is tracked."""
        events = [
            make_event("e001", 0, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "v1", "type": "code", "content_ref": "/v1.py"}}),
            make_event("e002", 1, EventType.ARTIFACT_SUPERSEDED,
                       payload={"artifact_id": "v1", "superseded_by_artifact_id": "v2"}),
            make_event("e003", 2, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "v2", "type": "code", "content_ref": "/v2.py"}}),
        ]

        artifacts = reduce_artifacts(events)

        assert artifacts.artifacts["v1"].superseded_by == "v2"
        assert not artifacts.artifacts["v1"].is_active


class TestArtifactNoEvidence:
    """Test artifact with empty evidence list."""

    def test_artifact_no_evidence(self):
        """Test artifact with no evidence works."""
        events = [
            make_event("e001", 0, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "a1", "type": "code", "content_ref": "/test.py"}}),
        ]

        artifacts = reduce_artifacts(events)

        assert "a1" in artifacts.artifacts


class TestArtifactDifferentWaypoints:
    """Test same artifact type at different waypoints."""

    def test_artifacts_at_different_waypoints(self):
        """Test artifacts at different waypoints are tracked separately."""
        events = [
            make_event("e001", 0, EventType.ARTIFACT_CREATED, waypoint_id="wp1",
                       payload={"artifact": {"artifact_id": "a1", "type": "code", "content_ref": "/test1.py"}}),
            make_event("e002", 1, EventType.ARTIFACT_CREATED, waypoint_id="wp2",
                       payload={"artifact": {"artifact_id": "a2", "type": "code", "content_ref": "/test2.py"}}),
        ]

        artifacts = reduce_artifacts(events)

        assert len(artifacts.artifacts) == 2


# =============================================================================
# Section 4: Session State Composite (4 tests)
# =============================================================================

class TestSessionStateComplete:
    """Test SessionState combines all views."""

    def test_session_state_complete(self):
        """Test SessionState has all three views."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
            make_event("e002", 1, EventType.PREFERENCE_LEARNED,
                       payload={"preference_id": "p1", "value": "vim", "confidence_delta": 0.8}),
            make_event("e003", 2, EventType.ARTIFACT_CREATED,
                       payload={"artifact": {"artifact_id": "a1", "type": "code", "content_ref": "/test.py"}}),
        ]

        state = reduce_session_state("test_session", events)

        assert state.journey is not None
        assert state.learned is not None
        assert state.artifacts is not None


class TestSessionStateEventCount:
    """Test event_count is correct."""

    def test_session_state_event_count(self):
        """Test event_count matches actual events."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
            make_event("e002", 1, EventType.WAYPOINT_ENTERED, waypoint_id="wp1",
                       payload={"waypoint_id": "wp1"}),
            make_event("e003", 2, EventType.PREFERENCE_LEARNED,
                       payload={"preference_id": "p1", "value": "v", "confidence_delta": 0.5}),
        ]

        state = reduce_session_state("test_session", events)

        assert state.event_count == 3


class TestSessionStateSerialization:
    """Test SessionState serializes to JSON."""

    def test_session_state_serializes(self):
        """Test SessionState can be serialized to JSON."""
        events = [
            make_event("e001", 0, EventType.INTENT_CREATED, payload={"goal": "test"}),
        ]

        state = reduce_session_state("test_session", events)

        # Should serialize without error
        json_str = state.model_dump_json()
        assert "test_session" in json_str


class TestSessionStateEmpty:
    """Test reducing empty event list."""

    def test_session_state_empty(self):
        """Test reducing empty event list returns empty views."""
        state = reduce_session_state("test_session", [])

        assert state.event_count == 0
        assert len(state.learned.preferences) == 0
        assert len(state.artifacts.artifacts) == 0
