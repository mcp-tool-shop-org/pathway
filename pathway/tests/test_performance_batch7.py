"""
Batch 7: Performance and remaining tests (25 tests)
Tests for performance, CLI entry point, and additional edge cases.
"""

import json
import time
import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

from pathway.store.sqlite_store import EventStore
from pathway.store.jsonl_io import export_session_jsonl, import_session_jsonl
from pathway.reducers.session import reduce_session_state
from pathway.models.events import (
    EventEnvelope, EventType, Actor, ActorKind,
)
from pathway.cli import main


# =============================================================================
# Helpers
# =============================================================================

def make_event(
    event_id: str,
    session_id: str = "test_session",
    seq: int = 0,
    event_type: EventType = EventType.INTENT_CREATED,
    head_id: str = "main",
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
        actor=Actor(kind=ActorKind.SYSTEM),
        payload=payload or {"goal": "test"},
    )


def run_cli(args):
    """Run CLI with given args and capture output."""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()

    try:
        with patch.object(sys, "argv", ["pathway"] + args):
            try:
                exit_code = main()
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
        stdout = sys.stdout.getvalue()
        stderr = sys.stderr.getvalue()
        return exit_code, stdout, stderr
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


# =============================================================================
# Section 1: Performance Tests (10 tests)
# =============================================================================

class TestLargeSessionPerformance:
    """Test performance with 10,000+ events."""

    def test_large_session_creation(self, tmp_path):
        """Test creating 10,000 events is fast enough."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        start = time.time()
        for i in range(10000):
            store.append(make_event(f"e{i:05d}", seq=i))
        elapsed = time.time() - start

        store.close()

        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30

    def test_large_session_query(self, tmp_path):
        """Test querying large session is fast."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create events
        for i in range(5000):
            store.append(make_event(f"e{i:05d}", seq=i))

        start = time.time()
        events = store.get_events("test_session")
        elapsed = time.time() - start

        store.close()

        assert len(events) == 5000
        # Query should be fast (< 5 seconds)
        assert elapsed < 5


class TestManySessionsPerformance:
    """Test performance with 1,000+ sessions."""

    def test_many_sessions_creation(self, tmp_path):
        """Test creating 1,000 sessions is fast."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        start = time.time()
        for i in range(1000):
            store.append(make_event(f"e{i}", session_id=f"sess_{i:04d}", seq=0))
        elapsed = time.time() - start

        store.close()

        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30

    def test_list_many_sessions(self, tmp_path):
        """Test listing 1,000 sessions is fast."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        for i in range(1000):
            store.append(make_event(f"e{i}", session_id=f"sess_{i:04d}", seq=0))

        start = time.time()
        sessions = store.list_sessions()
        elapsed = time.time() - start

        store.close()

        assert len(sessions) == 1000
        # Should be fast (< 1 second)
        assert elapsed < 1


class TestDeepBranchTreePerformance:
    """Test performance with deeply nested branches."""

    def test_many_branches(self, tmp_path):
        """Test handling 100 branches."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create events on 100 different branches
        for i in range(100):
            store.append(make_event(f"e{i:03d}", seq=i, head_id=f"branch_{i:03d}"))

        events = store.get_events("test_session")
        heads = store.get_all_heads("test_session")
        store.close()

        assert len(heads) == 100


class TestReductionPerformance:
    """Test reducer performance with large sessions."""

    def test_reduce_large_session(self, tmp_path):
        """Test reducing 5,000 events is fast."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        for i in range(5000):
            event_type = EventType.INTENT_CREATED if i == 0 else EventType.PREFERENCE_LEARNED
            payload = {"goal": "test"} if i == 0 else {
                "preference_id": f"p{i}", "value": f"v{i}", "confidence_delta": 0.5
            }
            store.append(make_event(f"e{i:05d}", seq=i, event_type=event_type, payload=payload))

        events = store.get_events("test_session")
        store.close()

        start = time.time()
        state = reduce_session_state("test_session", events)
        elapsed = time.time() - start

        # Should be fast (< 5 seconds)
        assert elapsed < 5
        assert state.event_count == 5000


class TestExportImportPerformance:
    """Test JSONL export/import performance."""

    def test_export_large_session(self, tmp_path):
        """Test exporting 5,000 events is fast."""
        db_path = tmp_path / "pathway.db"
        export_path = tmp_path / "export.jsonl"
        store = EventStore(db_path)

        for i in range(5000):
            store.append(make_event(f"e{i:05d}", seq=i))

        start = time.time()
        count = export_session_jsonl(store, "test_session", export_path)
        elapsed = time.time() - start

        store.close()

        assert count == 5000
        # Should be fast (< 5 seconds)
        assert elapsed < 5

    def test_import_large_file(self, tmp_path):
        """Test importing 5,000 events is fast."""
        db_path = tmp_path / "pathway.db"
        import_path = tmp_path / "import.jsonl"

        # Create JSONL file
        with open(import_path, "w") as f:
            for i in range(5000):
                event = {
                    "event_id": f"e{i:05d}",
                    "session_id": "test_session",
                    "seq": i,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "type": "IntentCreated",
                    "head_id": "main",
                    "actor": {"kind": "system"},
                    "payload": {"goal": f"test {i}"},
                }
                f.write(json.dumps(event) + "\n")

        store = EventStore(db_path)
        start = time.time()
        count = import_session_jsonl(store, import_path)
        elapsed = time.time() - start

        store.close()

        assert count == 5000
        # Should be fast (< 10 seconds)
        assert elapsed < 10


class TestDatabaseSizeGrowth:
    """Test database file size scales linearly."""

    def test_database_size_growth(self, tmp_path):
        """Test database size grows predictably."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        sizes = []
        for batch in range(5):
            for i in range(1000):
                idx = batch * 1000 + i
                store.append(make_event(f"e{idx:05d}", seq=idx))
            store.close()
            sizes.append(db_path.stat().st_size)
            store = EventStore(db_path)

        store.close()

        # Size should grow roughly linearly
        # Each batch should add roughly the same amount
        growth = [sizes[i] - sizes[i-1] for i in range(1, len(sizes))]
        avg_growth = sum(growth) / len(growth)
        # Allow 50% variance
        for g in growth:
            assert abs(g - avg_growth) < avg_growth * 0.5


class TestQueryWithIndexes:
    """Test indexed queries are fast."""

    def test_query_by_head(self, tmp_path):
        """Test filtering by head_id is fast."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create events on multiple heads
        for i in range(5000):
            head = f"head_{i % 10}"
            store.append(make_event(f"e{i:05d}", seq=i, head_id=head))

        start = time.time()
        events = store.get_events("test_session", head_id="head_0")
        elapsed = time.time() - start

        store.close()

        assert len(events) == 500
        # Should be fast (< 1 second)
        assert elapsed < 1


# =============================================================================
# Section 2: CLI Entry Point Tests (10 tests)
# =============================================================================

class TestCliHelp:
    """Test --help flag."""

    def test_cli_help(self):
        """Test --help shows usage."""
        exit_code, stdout, stderr = run_cli(["--help"])
        # argparse may return 0 or print to stdout
        assert "usage" in stdout.lower() or "pathway" in stdout.lower()


class TestCliNoCommand:
    """Test CLI with no command."""

    def test_cli_no_command(self):
        """Test CLI with no command shows help."""
        exit_code, stdout, stderr = run_cli([])
        assert exit_code == 0


class TestCliInvalidCommand:
    """Test invalid command."""

    def test_cli_invalid_command(self):
        """Test invalid command shows error."""
        exit_code, stdout, stderr = run_cli(["invalid_command"])
        # Should error
        assert exit_code != 0 or "error" in stderr.lower() or "invalid" in stderr.lower()


class TestCliMissingRequiredArgs:
    """Test command with missing args."""

    def test_cli_export_missing_session(self, tmp_path):
        """Test export without session_id errors."""
        db_path = tmp_path / "pathway.db"
        EventStore(db_path).close()

        # export requires session_id
        exit_code, stdout, stderr = run_cli(["--db", str(db_path), "export"])
        # Should error due to missing args
        assert exit_code != 0 or "error" in stderr.lower()


class TestCliDatabaseArgGlobal:
    """Test --db flag works for all commands."""

    def test_db_flag_with_init(self, tmp_path):
        """Test --db flag works with init command."""
        custom_db = tmp_path / "custom.db"

        exit_code, stdout, stderr = run_cli(["--db", str(custom_db), "init"])

        assert exit_code == 0
        assert custom_db.exists()

    def test_db_flag_with_sessions(self, tmp_path):
        """Test --db flag works with sessions command."""
        custom_db = tmp_path / "custom.db"
        EventStore(custom_db).close()

        exit_code, stdout, stderr = run_cli(["--db", str(custom_db), "sessions"])

        assert exit_code == 0


class TestCliInitSubcommand:
    """Test init subcommand."""

    def test_init_subcommand(self, tmp_path):
        """Test init creates database."""
        db_path = tmp_path / "test.db"

        exit_code, stdout, stderr = run_cli(["--db", str(db_path), "init"])

        assert exit_code == 0
        assert db_path.exists()


class TestCliSessionsSubcommand:
    """Test sessions subcommand."""

    def test_sessions_subcommand(self, tmp_path):
        """Test sessions lists sessions."""
        db_path = tmp_path / "test.db"
        store = EventStore(db_path)
        store.append(make_event("e001", session_id="my_session", seq=0))
        store.close()

        exit_code, stdout, stderr = run_cli(["--db", str(db_path), "sessions"])

        assert exit_code == 0
        assert "my_session" in stdout


class TestCliDoctorSubcommand:
    """Test doctor subcommand."""

    def test_doctor_subcommand(self, tmp_path):
        """Test doctor checks database health."""
        db_path = tmp_path / "test.db"
        store = EventStore(db_path)
        store.append(make_event("e001", seq=0))
        store.close()

        exit_code, stdout, stderr = run_cli(["--db", str(db_path), "doctor"])

        assert exit_code == 0
        assert "HEALTHY" in stdout


# =============================================================================
# Section 3: Additional Edge Cases (5 tests)
# =============================================================================

class TestStoreGetEventNotFound:
    """Test get_event for non-existent event."""

    def test_get_event_not_found(self, tmp_path):
        """Test get_event returns None for missing event."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        event = store.get_event("nonexistent")

        assert event is None
        store.close()


class TestStoreGetHeadTipNoEvents:
    """Test get_head_tip with no events on head."""

    def test_get_head_tip_no_events(self, tmp_path):
        """Test get_head_tip returns None for head with no events."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)
        store.append(make_event("e001", seq=0, head_id="main"))

        tip = store.get_head_tip("test_session", "nonexistent_head")

        assert tip is None
        store.close()


class TestStoreGetNextSeqNewSession:
    """Test get_next_seq for new session."""

    def test_get_next_seq_new_session(self, tmp_path):
        """Test get_next_seq returns 0 for new session."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        seq = store.get_next_seq("new_session")

        assert seq == 0
        store.close()


class TestEventWithAllOptionalFields:
    """Test event with all optional fields."""

    def test_event_all_optional_fields(self, tmp_path):
        """Test event with all optional fields set."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        event = EventEnvelope(
            event_id="e001",
            session_id="test_session",
            seq=0,
            ts=datetime.now(timezone.utc),
            type=EventType.WAYPOINT_ENTERED,
            head_id="main",
            parent_event_id="parent123",
            waypoint_id="wp123",
            actor=Actor(kind=ActorKind.USER, id="user123"),
            payload={"waypoint_id": "wp123"},
        )
        store.append(event)

        retrieved = store.get_event("e001")
        assert retrieved.parent_event_id == "parent123"
        assert retrieved.waypoint_id == "wp123"
        assert retrieved.actor.id == "user123"

        store.close()


class TestReducerWithMixedEventTypes:
    """Test reducer with all event types mixed."""

    def test_reducer_mixed_event_types(self, tmp_path):
        """Test reducer handles all event types together."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create events of various types
        events_data = [
            (EventType.INTENT_CREATED, {"goal": "test"}),
            (EventType.WAYPOINT_ENTERED, {"waypoint_id": "wp1"}),
            (EventType.PREFERENCE_LEARNED, {"preference_id": "p1", "value": "v", "confidence_delta": 0.5}),
            (EventType.ARTIFACT_CREATED, {"artifact": {"artifact_id": "a1", "type": "code", "content_ref": "/test.py"}}),
            (EventType.CONSTRAINT_LEARNED, {"constraint_id": "c1", "value": "Python", "confidence_delta": 0.9}),
        ]

        for i, (event_type, payload) in enumerate(events_data):
            store.append(make_event(f"e{i:03d}", seq=i, event_type=event_type, payload=payload))

        events = store.get_events("test_session")
        state = reduce_session_state("test_session", events)
        store.close()

        assert state.event_count == 5
        assert len(state.learned.preferences) >= 1
        assert len(state.artifacts.artifacts) >= 1
