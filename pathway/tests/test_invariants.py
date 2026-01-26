"""Invariant tests for Pathway core guarantees.

These tests verify the fundamental invariants that must hold:
1. Seq is monotonic and atomic
2. Append-only (no updates/deletes)
3. Backtrack creates new history, doesn't rewrite
4. Learned aggregates across ALL events (independent of head)
5. Evidence refs tolerate missing targets
"""

import pytest
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from pathway.models.events import (
    EventEnvelope,
    EventType,
    Actor,
    ActorKind,
    EvidenceRef,
)
from pathway.store.sqlite_store import EventStore
from pathway.reducers.session import reduce_session_state
from pathway.reducers.learned import reduce_learned


def make_event(
    event_id: str,
    event_type: EventType,
    seq: int,
    payload: dict,
    session_id: str = "test",
    head_id: str = "main",
    parent_event_id: str | None = None,
    waypoint_id: str | None = None,
) -> EventEnvelope:
    """Helper to create test events."""
    return EventEnvelope(
        event_id=event_id,
        session_id=session_id,
        seq=seq,
        ts=datetime.now(timezone.utc) + timedelta(seconds=seq),
        type=event_type,
        head_id=head_id,
        parent_event_id=parent_event_id,
        waypoint_id=waypoint_id,
        actor=Actor(kind=ActorKind.SYSTEM),
        payload=payload,
    )


class TestSeqMonotonicAndAtomic:
    """Invariant 1: Seq is monotonic, unique per session, atomically assigned."""

    def test_seq_unique_constraint(self):
        """Duplicate seq in same session must fail."""
        store = EventStore(":memory:")
        store.append(make_event("e1", EventType.INTENT_CREATED, 0, {"goal": "test"}))

        with pytest.raises(ValueError):
            store.append(make_event("e2", EventType.INTENT_CREATED, 0, {"goal": "test2"}))

    def test_seq_can_duplicate_across_sessions(self):
        """Same seq in different sessions is OK."""
        store = EventStore(":memory:")
        store.append(make_event("e1", EventType.INTENT_CREATED, 0, {"goal": "test"}, session_id="sess1"))
        store.append(make_event("e2", EventType.INTENT_CREATED, 0, {"goal": "test"}, session_id="sess2"))

        assert len(store.get_events("sess1")) == 1
        assert len(store.get_events("sess2")) == 1

    def test_concurrent_seq_assignment(self):
        """Concurrent writers should not produce duplicate seqs.

        Uses auto_seq=True for atomic seq assignment.
        """
        store = EventStore(":memory:")
        errors = []
        successful_seqs = []

        def write_event(i: int):
            try:
                event = make_event(
                    f"e{i:04d}",
                    EventType.WAYPOINT_ENTERED,
                    0,  # placeholder, will be replaced by auto_seq
                    {"waypoint_id": f"w{i}"},
                    session_id="concurrent_test",
                )
                result = store.append(event, auto_seq=True)
                return result.seq
            except Exception as e:
                errors.append((i, str(e)))
                return None

        # Run 20 concurrent writes
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(write_event, i) for i in range(20)]
            for future in as_completed(futures):
                seq = future.result()
                if seq is not None:
                    successful_seqs.append(seq)

        # With atomic seq assignment, ALL should succeed
        assert len(successful_seqs) == 20, f"Expected 20 successes, got {len(successful_seqs)}, errors: {errors}"

        # No duplicate seqs
        assert len(successful_seqs) == len(set(successful_seqs)), "Duplicate seqs detected!"

        # All seqs should be contiguous [0, 20)
        events = store.get_events("concurrent_test")
        actual_seqs = sorted([e.seq for e in events])
        assert actual_seqs == list(range(20)), "Seqs should be contiguous 0-19"


class TestAppendOnlyInvariant:
    """Invariant 2: Events are never modified or deleted."""

    def test_event_id_cannot_be_reused(self):
        """Same event_id cannot be inserted twice."""
        store = EventStore(":memory:")
        store.append(make_event("e1", EventType.INTENT_CREATED, 0, {"goal": "original"}))

        with pytest.raises(ValueError):
            store.append(make_event("e1", EventType.INTENT_CREATED, 1, {"goal": "modified"}))

    def test_event_content_immutable(self):
        """Once stored, event content cannot change."""
        store = EventStore(":memory:")
        original_payload = {"goal": "original"}
        store.append(make_event("e1", EventType.INTENT_CREATED, 0, original_payload))

        # Retrieve and verify
        retrieved = store.get_event("e1")
        assert retrieved.payload["goal"] == "original"

        # Modifying the dict in memory doesn't affect stored data
        original_payload["goal"] = "hacked"
        retrieved2 = store.get_event("e1")
        assert retrieved2.payload["goal"] == "original"


class TestBacktrackSemantics:
    """Invariant 3: Backtrack creates new events, doesn't rewrite history."""

    def test_backtrack_preserves_original_events(self):
        """After backtracking, original events still exist and are queryable."""
        store = EventStore(":memory:")

        # Build initial path: w0 -> w1 -> w2
        events = [
            make_event("e1", EventType.WAYPOINT_ENTERED, 0, {"waypoint_id": "w0", "via": "next"}, waypoint_id="w0"),
            make_event("e2", EventType.WAYPOINT_ENTERED, 1, {"waypoint_id": "w1", "via": "next"}, waypoint_id="w1", parent_event_id="e1"),
            make_event("e3", EventType.WAYPOINT_ENTERED, 2, {"waypoint_id": "w2", "via": "next"}, waypoint_id="w2", parent_event_id="e2"),
        ]
        for e in events:
            store.append(e)

        # Backtrack from e3 to e1
        backtrack = make_event(
            "e4",
            EventType.BACKTRACKED,
            3,
            {"from_event_id": "e3", "to_event_id": "e1", "mode": "jump", "keep_artifacts": "all"},
            parent_event_id="e3",
        )
        store.append(backtrack)

        # ALL original events should still exist
        all_events = store.get_events("test")
        assert len(all_events) == 4
        assert {e.event_id for e in all_events} == {"e1", "e2", "e3", "e4"}

    def test_backtrack_then_diverge_creates_new_branch(self):
        """After backtrack, new work on divergent path should create new head."""
        events = [
            # Initial path on main
            make_event("e1", EventType.WAYPOINT_ENTERED, 0, {"waypoint_id": "w0"}, head_id="main"),
            make_event("e2", EventType.WAYPOINT_ENTERED, 1, {"waypoint_id": "w1"}, head_id="main", parent_event_id="e1"),
            make_event("e3", EventType.WAYPOINT_ENTERED, 2, {"waypoint_id": "w2"}, head_id="main", parent_event_id="e2"),

            # Backtrack to e1
            make_event("e4", EventType.BACKTRACKED, 3,
                      {"from_event_id": "e3", "to_event_id": "e1", "mode": "jump", "keep_artifacts": "all"},
                      head_id="main", parent_event_id="e3"),

            # New work diverging from e1 (should be on new branch b1)
            make_event("e5", EventType.WAYPOINT_ENTERED, 4, {"waypoint_id": "w3"}, head_id="b1", parent_event_id="e1"),
        ]

        state = reduce_session_state("test", events)

        # Both branches should have tips
        assert "main" in state.journey.branch_tips
        assert "b1" in state.journey.branch_tips

        # Active head should be b1 (latest event)
        assert state.journey.active_head_id == "b1"


class TestLearnedIndependenceOfHead:
    """Invariant 4: Learned state aggregates across ALL events, regardless of head."""

    def test_learning_on_abandoned_branch_persists(self):
        """Concepts learned on a failed branch remain after backtracking."""
        events = [
            # Start on main
            make_event("e1", EventType.WAYPOINT_ENTERED, 0, {"waypoint_id": "w0"}, head_id="main"),

            # Learn concept on main
            make_event("e2", EventType.CONCEPT_LEARNED, 1,
                      {"concept_id": "concept.input_output", "confidence_delta": 0.3},
                      head_id="main", parent_event_id="e1"),

            # Go to w1, hit a problem
            make_event("e3", EventType.WAYPOINT_ENTERED, 2, {"waypoint_id": "w1"}, head_id="main", parent_event_id="e2"),
            make_event("e4", EventType.CONCEPT_LEARNED, 3,
                      {"concept_id": "concept.dependencies", "confidence_delta": 0.4},
                      head_id="main", parent_event_id="e3"),

            # Backtrack to w0
            make_event("e5", EventType.BACKTRACKED, 4,
                      {"from_event_id": "e4", "to_event_id": "e1", "mode": "jump", "keep_artifacts": "all"},
                      head_id="main", parent_event_id="e4"),

            # Continue on new branch b1
            make_event("e6", EventType.WAYPOINT_ENTERED, 5, {"waypoint_id": "w2"}, head_id="b1", parent_event_id="e1"),
        ]

        state = reduce_session_state("test", events)

        # BOTH concepts should be present (learned on "abandoned" path)
        assert "concept.input_output" in state.learned.concepts
        assert "concept.dependencies" in state.learned.concepts
        assert state.learned.concepts["concept.input_output"].confidence == 0.3
        assert state.learned.concepts["concept.dependencies"].confidence == 0.4

    def test_learning_accumulates_across_branches(self):
        """Same concept learned on multiple branches accumulates."""
        events = [
            make_event("e1", EventType.WAYPOINT_ENTERED, 0, {"waypoint_id": "w0"}, head_id="main"),

            # Learn on main
            make_event("e2", EventType.CONCEPT_LEARNED, 1,
                      {"concept_id": "concept.functions", "confidence_delta": 0.2},
                      head_id="main"),

            # Switch to branch b1
            make_event("e3", EventType.WAYPOINT_ENTERED, 2, {"waypoint_id": "w1"}, head_id="b1"),

            # Learn same concept on b1
            make_event("e4", EventType.CONCEPT_LEARNED, 3,
                      {"concept_id": "concept.functions", "confidence_delta": 0.3},
                      head_id="b1"),
        ]

        state = reduce_session_state("test", events)

        # Confidence should be cumulative: 0.2 + 0.3 = 0.5
        assert state.learned.concepts["concept.functions"].confidence == 0.5


class TestEvidenceRefTolerance:
    """Invariant 5: Dangling evidence refs don't crash reducers."""

    def test_missing_artifact_evidence(self):
        """ConceptLearned with evidence pointing to non-existent artifact."""
        events = [
            make_event("e1", EventType.CONCEPT_LEARNED, 0, {
                "concept_id": "concept.test",
                "confidence_delta": 0.5,
                "evidence": [{"kind": "artifact", "id": "nonexistent_artifact", "note": "missing"}],
            }),
        ]

        # Should not crash
        state = reduce_session_state("test", events)
        assert state.learned.concepts["concept.test"].confidence == 0.5
        # Evidence ref is stored even if target doesn't exist
        assert len(state.learned.concepts["concept.test"].evidence) == 1

    def test_missing_event_evidence(self):
        """ConceptLearned with evidence pointing to non-existent event."""
        events = [
            make_event("e1", EventType.CONCEPT_LEARNED, 0, {
                "concept_id": "concept.test",
                "confidence_delta": 0.5,
                "evidence": [{"kind": "event", "id": "e999", "note": "missing event"}],
            }),
        ]

        # Should not crash
        state = reduce_session_state("test", events)
        assert state.learned.concepts["concept.test"].confidence == 0.5

    def test_superseded_artifact_reference(self):
        """Referencing a superseded artifact should still work."""
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
            # Reference the superseded artifact
            make_event("e4", EventType.CONCEPT_LEARNED, 3, {
                "concept_id": "concept.test",
                "confidence_delta": 0.3,
                "evidence": [{"kind": "artifact", "id": "a1", "note": "old but valid"}],
            }),
        ]

        state = reduce_session_state("test", events)

        # Should work fine - evidence points to superseded (but existing) artifact
        assert state.learned.concepts["concept.test"].confidence == 0.3
        assert not state.artifacts.artifacts["a1"].is_active
        assert state.artifacts.artifacts["a2"].is_active
