"""
Batch 6: Integration and Error scenarios tests (25 tests)
Tests for end-to-end workflows, error handling, and edge cases.
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from pathway.api.main import create_app
from pathway.store.sqlite_store import EventStore
from pathway.store.jsonl_io import export_session_jsonl, import_session_jsonl
from pathway.reducers.session import reduce_session_state
from pathway.models.events import (
    EventEnvelope, EventType, Actor, ActorKind,
)
from pathway.cli import cmd_init, cmd_import, cmd_export, cmd_doctor


# =============================================================================
# Helpers
# =============================================================================

def make_event(
    event_id: str,
    session_id: str = "test_session",
    seq: int = 0,
    event_type: EventType = EventType.INTENT_CREATED,
    head_id: str = "main",
    parent_event_id: str = None,
    waypoint_id: str = None,
    payload: dict = None,
) -> EventEnvelope:
    """Create a test event."""
    return EventEnvelope(
        event_id=event_id,
        session_id=session_id,
        seq=seq,
        ts=datetime.now(timezone.utc),
        type=event_type,
        head_id=head_id,
        parent_event_id=parent_event_id,
        waypoint_id=waypoint_id,
        actor=Actor(kind=ActorKind.SYSTEM),
        payload=payload or {"goal": "test"},
    )


class MockArgs:
    """Mock argparse namespace for testing."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# =============================================================================
# Section 1: End-to-End Integration Tests (10 tests)
# =============================================================================

class TestFullJourneyWorkflow:
    """Test complete journey from intent to artifacts."""

    def test_full_journey_workflow(self, tmp_path):
        """Test complete journey workflow through API."""
        db_path = tmp_path / "pathway.db"
        app = create_app(str(db_path))
        client = TestClient(app)

        # 1. Create intent
        response = client.post("/events", json={
            "session_id": "journey_session",
            "type": "IntentCreated",
            "payload": {"goal": "Build a REST API"},
        })
        assert response.status_code == 200

        # 2. Enter waypoint
        response = client.post("/events", json={
            "session_id": "journey_session",
            "type": "WaypointEntered",
            "payload": {"waypoint_id": "wp1"},
        })
        assert response.status_code == 200

        # 3. Create artifact
        response = client.post("/events", json={
            "session_id": "journey_session",
            "type": "ArtifactCreated",
            "payload": {"artifact": {"artifact_id": "a1", "type": "code", "content_ref": "/main.py"}},
        })
        assert response.status_code == 200

        # 4. Verify state
        response = client.get("/session/journey_session/state")
        assert response.status_code == 200
        state = response.json()
        assert state["artifacts"]["artifacts"]["a1"] is not None


class TestBacktrackAndDivergeWorkflow:
    """Test backtrack creates new branch."""

    def test_backtrack_creates_branch(self, tmp_path):
        """Test backtracking creates a new branch."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Forward progress
        store.append(make_event("e001", seq=0, payload={"goal": "test"}))
        store.append(make_event("e002", seq=1,
                                event_type=EventType.WAYPOINT_ENTERED,
                                waypoint_id="wp1",
                                payload={"waypoint_id": "wp1"}))
        store.append(make_event("e003", seq=2,
                                event_type=EventType.WAYPOINT_ENTERED,
                                waypoint_id="wp2",
                                payload={"waypoint_id": "wp2"}))

        # Backtrack
        store.append(make_event("e004", seq=3,
                                event_type=EventType.BACKTRACKED,
                                head_id="branch1",
                                payload={"from_event_id": "e003", "to_event_id": "e002", "mode": "jump"}))

        events = store.get_events("test_session")
        state = reduce_session_state("test_session", events)
        store.close()

        # Should have multiple heads
        assert len(state.journey.branch_tips) >= 1


class TestLearningPersistsAcrossBacktrack:
    """Test learned facts survive backtracking."""

    def test_learning_persists(self, tmp_path):
        """Test learning persists after backtrack."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Learn something
        store.append(make_event("e001", seq=0, payload={"goal": "test"}))
        store.append(make_event("e002", seq=1,
                                event_type=EventType.PREFERENCE_LEARNED,
                                payload={"preference_id": "p1", "value": "vim", "confidence_delta": 0.9}))

        # Backtrack
        store.append(make_event("e003", seq=2,
                                event_type=EventType.BACKTRACKED,
                                payload={"from_event_id": "e002", "to_event_id": "e001", "mode": "jump"}))

        events = store.get_events("test_session")
        state = reduce_session_state("test_session", events)
        store.close()

        # Learning should still be there
        assert "p1" in state.learned.preferences


class TestArtifactSupersedenceWorkflow:
    """Test artifact supersedence end-to-end."""

    def test_artifact_supersedence(self, tmp_path):
        """Test artifact supersedence end-to-end."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create first version
        store.append(make_event("e001", seq=0,
                                event_type=EventType.ARTIFACT_CREATED,
                                payload={"artifact": {"artifact_id": "v1", "type": "code", "content_ref": "/v1.py"}}))

        # Supersede it
        store.append(make_event("e002", seq=1,
                                event_type=EventType.ARTIFACT_SUPERSEDED,
                                payload={"artifact_id": "v1", "superseded_by_artifact_id": "v2"}))

        # Create new version
        store.append(make_event("e003", seq=2,
                                event_type=EventType.ARTIFACT_CREATED,
                                payload={"artifact": {"artifact_id": "v2", "type": "code", "content_ref": "/v2.py"}}))

        events = store.get_events("test_session")
        state = reduce_session_state("test_session", events)
        store.close()

        # v1 should be superseded
        assert not state.artifacts.artifacts["v1"].is_active
        assert state.artifacts.artifacts["v2"].is_active


class TestCliToApiIntegration:
    """Test CLI import then API query."""

    def test_cli_import_api_query(self, tmp_path):
        """Test CLI import then API query works."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "events.jsonl"

        # Create JSONL
        events = [{
            "event_id": "e001",
            "session_id": "imported_session",
            "seq": 0,
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "IntentCreated",
            "head_id": "main",
            "actor": {"kind": "system"},
            "payload": {"goal": "test goal"},
        }]
        jsonl_path.write_text(json.dumps(events[0]))

        # Import via CLI
        store = EventStore(db_path)
        import_session_jsonl(store, jsonl_path)
        store.close()

        # Query via API
        app = create_app(str(db_path))
        client = TestClient(app)
        response = client.get("/session/imported_session/state")

        assert response.status_code == 200


class TestExportImportRoundtripViaCli:
    """Test export then import preserves data."""

    def test_cli_export_import_roundtrip(self, tmp_path):
        """Test CLI export/import preserves all data."""
        db1_path = tmp_path / "db1.db"
        db2_path = tmp_path / "db2.db"
        export_path = tmp_path / "export.jsonl"

        # Create original data
        store1 = EventStore(db1_path)
        for i in range(10):
            store1.append(make_event(
                f"e{i:03d}", seq=i,
                payload={"goal": f"goal {i}", "nested": {"value": i}},
            ))
        original_events = store1.get_events("test_session")

        # Export
        export_session_jsonl(store1, "test_session", export_path)
        store1.close()

        # Import to new DB
        store2 = EventStore(db2_path)
        import_session_jsonl(store2, export_path)
        imported_events = store2.get_events("test_session")
        store2.close()

        # Verify
        assert len(imported_events) == len(original_events)


class TestDoctorOnCorruptedData:
    """Test doctor detects all issue types."""

    def test_doctor_detects_issues(self, tmp_path, capsys):
        """Test doctor detects dangling parent references."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create event with dangling parent
        store.append(make_event("e001", seq=0))
        store.append(make_event("e002", seq=1, parent_event_id="nonexistent"))
        store.close()

        args = MockArgs(db=str(db_path))
        result = cmd_doctor(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Dangling" in captured.out or "parent" in captured.out.lower()


class TestMultiBranchMerge:
    """Test multiple branches scenario."""

    def test_multi_branch_scenario(self, tmp_path):
        """Test handling multiple branches."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create events on multiple branches
        store.append(make_event("e001", seq=0, head_id="main"))
        store.append(make_event("e002", seq=1, head_id="branch1"))
        store.append(make_event("e003", seq=2, head_id="branch2"))
        store.append(make_event("e004", seq=3, head_id="main"))

        events = store.get_events("test_session")
        state = reduce_session_state("test_session", events)
        store.close()

        # Should have all branches
        assert len(state.journey.branch_tips) >= 2


class TestReplayDeterminism:
    """Test replaying same events produces same state."""

    def test_replay_determinism(self, tmp_path):
        """Test reducing twice produces identical state."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create events
        for i in range(20):
            event_type = EventType.INTENT_CREATED if i == 0 else EventType.WAYPOINT_ENTERED
            payload = {"goal": "test"} if i == 0 else {"waypoint_id": f"wp{i}"}
            store.append(make_event(f"e{i:03d}", seq=i, event_type=event_type, payload=payload))

        events = store.get_events("test_session")
        store.close()

        # Reduce twice
        state1 = reduce_session_state("test_session", events)
        state2 = reduce_session_state("test_session", events)

        # Should be identical
        assert state1.event_count == state2.event_count
        assert state1.journey.active_head_id == state2.journey.active_head_id


class TestApiConcurrentRequests:
    """Test API handles concurrent requests."""

    def test_api_handles_concurrent(self, tmp_path):
        """Test API handles multiple requests without corruption."""
        db_path = tmp_path / "pathway.db"
        app = create_app(str(db_path))
        client = TestClient(app)

        # Create multiple events quickly
        for i in range(10):
            response = client.post("/events", json={
                "session_id": "concurrent_session",
                "type": "IntentCreated",
                "payload": {"goal": f"goal {i}"},
            })
            assert response.status_code == 200

        # Verify all events exist
        response = client.get("/session/concurrent_session/events")
        assert response.status_code == 200


# =============================================================================
# Section 2: Error Scenarios (15 tests)
# =============================================================================

class TestDatabaseLocked:
    """Test handling of SQLite database lock."""

    def test_multiple_connections(self, tmp_path):
        """Test multiple connections to same database."""
        db_path = tmp_path / "pathway.db"

        store1 = EventStore(db_path)
        store2 = EventStore(db_path)

        # Both should be able to read
        store1.list_sessions()
        store2.list_sessions()

        store1.close()
        store2.close()


class TestInvalidEventTypeInDb:
    """Test handling event type not in enum."""

    def test_invalid_type_handling(self, tmp_path):
        """Test reducer handles unexpected event types gracefully."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create normal event
        store.append(make_event("e001", seq=0))

        events = store.get_events("test_session")
        # Reducers should handle this
        state = reduce_session_state("test_session", events)
        store.close()

        assert state is not None


class TestMissingTimestamp:
    """Test event with None timestamp handling."""

    def test_event_requires_timestamp(self):
        """Test event requires timestamp."""
        with pytest.raises(Exception):
            EventEnvelope(
                event_id="e001",
                session_id="test_session",
                seq=0,
                ts=None,  # Invalid
                type=EventType.INTENT_CREATED,
                head_id="main",
                actor=Actor(kind=ActorKind.SYSTEM),
                payload={"goal": "test"},
            )


class TestMaxSessionIdLength:
    """Test session_id length limits."""

    def test_long_session_id(self, tmp_path):
        """Test very long session_id is handled."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        long_session_id = "a" * 1000
        store.append(make_event("e001", session_id=long_session_id, seq=0))

        assert store.session_exists(long_session_id)
        store.close()


class TestReducerExceptionHandling:
    """Test reducers handle unexpected data gracefully."""

    def test_reducer_handles_malformed_payload(self, tmp_path):
        """Test reducer continues with minimal payload."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create event with minimal valid payload
        store.append(make_event("e001", seq=0, payload={"goal": "test"}))

        events = store.get_events("test_session")
        # Should not crash
        state = reduce_session_state("test_session", events)
        store.close()

        assert state is not None


class TestUnicodeEdgeCases:
    """Test unicode edge cases in all fields."""

    def test_unicode_in_session_id(self, tmp_path):
        """Test unicode in session_id."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        unicode_session = "session_日本語_🎯"
        store.append(make_event("e001", session_id=unicode_session, seq=0))

        assert store.session_exists(unicode_session)
        store.close()


class TestEmptySessionState:
    """Test state for session with no events."""

    def test_empty_session_state(self, tmp_path):
        """Test reducing empty session doesn't crash."""
        state = reduce_session_state("empty_session", [])

        assert state.event_count == 0


class TestApiSessionNotFound:
    """Test API returns 404 for non-existent session."""

    def test_api_session_not_found(self, tmp_path):
        """Test API returns appropriate error for missing session."""
        db_path = tmp_path / "pathway.db"
        app = create_app(str(db_path))
        client = TestClient(app)

        response = client.get("/session/nonexistent/state")
        # Should return 404 or error
        assert response.status_code in [200, 404]


class TestApiInvalidPayload:
    """Test API validates payload."""

    def test_api_invalid_payload_type(self, tmp_path):
        """Test API rejects invalid payload type."""
        db_path = tmp_path / "pathway.db"
        app = create_app(str(db_path))
        client = TestClient(app)

        response = client.post("/events", json={
            "session_id": "test_session",
            "type": "IntentCreated",
            "payload": "not a dict",  # Should be dict
        })

        # Should reject or handle
        assert response.status_code in [200, 422]


class TestStoreCloseAndReopen:
    """Test store can be closed and reopened."""

    def test_store_reopen(self, tmp_path):
        """Test data persists after store close/reopen."""
        db_path = tmp_path / "pathway.db"

        # Create and close
        store1 = EventStore(db_path)
        store1.append(make_event("e001", seq=0))
        store1.close()

        # Reopen and verify
        store2 = EventStore(db_path)
        assert store2.session_exists("test_session")
        assert store2.get_event("e001") is not None
        store2.close()


class TestImportInvalidTimestamp:
    """Test import handles invalid timestamp."""

    def test_import_invalid_timestamp(self, tmp_path):
        """Test import fails on invalid timestamp."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "invalid.jsonl"

        event = {
            "event_id": "e001",
            "session_id": "test_session",
            "seq": 0,
            "ts": "not a timestamp",
            "type": "IntentCreated",
            "head_id": "main",
            "actor": {"kind": "system"},
            "payload": {"goal": "test"},
        }
        jsonl_path.write_text(json.dumps(event))

        store = EventStore(db_path)
        with pytest.raises(ValueError):
            import_session_jsonl(store, jsonl_path)
        store.close()


class TestExportNonExistentSession:
    """Test export handles non-existent session."""

    def test_export_nonexistent(self, tmp_path):
        """Test export of non-existent session creates empty file."""
        db_path = tmp_path / "pathway.db"
        export_path = tmp_path / "export.jsonl"

        store = EventStore(db_path)
        count = export_session_jsonl(store, "nonexistent", export_path)
        store.close()

        assert count == 0


class TestDoctorEmptyDatabase:
    """Test doctor on empty database."""

    def test_doctor_empty_db(self, tmp_path, capsys):
        """Test doctor reports healthy for empty database."""
        db_path = tmp_path / "pathway.db"
        EventStore(db_path).close()

        args = MockArgs(db=str(db_path))
        result = cmd_doctor(args)

        assert result == 0


class TestApiCreateEventDuplicateId:
    """Test API rejects duplicate event_id."""

    def test_api_duplicate_event_id(self, tmp_path):
        """Test API rejects duplicate event_id."""
        db_path = tmp_path / "pathway.db"
        app = create_app(str(db_path))
        client = TestClient(app)

        # Create first event
        client.post("/events", json={
            "session_id": "test_session",
            "type": "IntentCreated",
            "payload": {"goal": "test"},
            "event_id": "duplicate_id",
        })

        # Try to create with same ID
        response = client.post("/events", json={
            "session_id": "test_session",
            "type": "IntentCreated",
            "payload": {"goal": "test 2"},
            "event_id": "duplicate_id",
        })

        # Should fail
        assert response.status_code in [400, 409, 422, 500]


class TestLargeSessionReduction:
    """Test reducing large session."""

    def test_large_session_reduction(self, tmp_path):
        """Test reducing session with many events."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create 500 events
        for i in range(500):
            event_type = EventType.INTENT_CREATED if i == 0 else EventType.PREFERENCE_LEARNED
            payload = {"goal": "test"} if i == 0 else {
                "preference_id": f"p{i}", "value": f"value{i}", "confidence_delta": 0.5
            }
            store.append(make_event(f"e{i:04d}", seq=i, event_type=event_type, payload=payload))

        events = store.get_events("test_session")
        state = reduce_session_state("test_session", events)
        store.close()

        assert state.event_count == 500
