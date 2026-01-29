"""
Batch 3: JSONL I/O and Store edge cases (25 tests)
Tests for JSONL import/export and SQLite store edge cases.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import threading

from pathway.store.sqlite_store import EventStore
from pathway.store.jsonl_io import (
    export_session_jsonl,
    import_session_jsonl,
    export_all_sessions_jsonl,
    import_all_jsonl_files,
)
from pathway.models.events import EventEnvelope, EventType, Actor, ActorKind


# =============================================================================
# Helpers
# =============================================================================

def make_test_event(
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


# =============================================================================
# Section 1: JSONL Export Functionality (7 tests)
# =============================================================================

class TestExportSessionJsonl:
    """Test exporting session to JSONL file."""

    def test_export_session_jsonl(self, tmp_path):
        """Test exporting session creates valid JSONL."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        store = EventStore(db_path)
        for i in range(3):
            store.append(make_test_event(f"e{i:03d}", seq=i))

        count = export_session_jsonl(store, "test_session", output_path)
        store.close()

        assert count == 3
        assert output_path.exists()


class TestExportPreservesOrder:
    """Test events are exported in seq order."""

    def test_export_preserves_order(self, tmp_path):
        """Test events are exported in ascending seq order."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        store = EventStore(db_path)
        # Insert out of order
        store.append(make_test_event("e003", seq=2))
        store.append(make_test_event("e001", seq=0))
        store.append(make_test_event("e002", seq=1))

        export_session_jsonl(store, "test_session", output_path)
        store.close()

        lines = output_path.read_text().strip().split("\n")
        seqs = [json.loads(line)["seq"] for line in lines]
        assert seqs == [0, 1, 2]


class TestExportPreservesAllFields:
    """Test all event fields are preserved."""

    def test_export_preserves_fields(self, tmp_path):
        """Test all required fields are in exported JSON."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        store = EventStore(db_path)
        store.append(make_test_event("e001", seq=0, payload={"goal": "test goal"}))

        export_session_jsonl(store, "test_session", output_path)
        store.close()

        data = json.loads(output_path.read_text().strip())
        required_fields = ["event_id", "session_id", "seq", "ts", "type", "head_id", "actor", "payload"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestExportCreatesDirectory:
    """Test export creates output directory if needed."""

    def test_export_creates_directory(self, tmp_path):
        """Test export creates parent directories."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "subdir" / "nested" / "output.jsonl"

        store = EventStore(db_path)
        store.append(make_test_event("e001", seq=0))

        export_session_jsonl(store, "test_session", output_path)
        store.close()

        assert output_path.exists()


class TestExportOverwritesExisting:
    """Test export overwrites existing file."""

    def test_export_overwrites_existing(self, tmp_path):
        """Test export replaces existing file."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        output_path.write_text("old content\n")

        store = EventStore(db_path)
        store.append(make_test_event("e001", seq=0))

        export_session_jsonl(store, "test_session", output_path)
        store.close()

        content = output_path.read_text()
        assert "old content" not in content
        assert "e001" in content


class TestExportAllSessions:
    """Test exporting all sessions to directory."""

    def test_export_all_sessions(self, tmp_path):
        """Test exporting all sessions creates one file per session."""
        db_path = tmp_path / "pathway.db"
        output_dir = tmp_path / "exports"

        store = EventStore(db_path)
        for sess in ["sess1", "sess2", "sess3"]:
            for i in range(2):
                store.append(make_test_event(f"{sess}_e{i}", session_id=sess, seq=i))

        results = export_all_sessions_jsonl(store, output_dir)
        store.close()

        assert len(results) == 3
        assert (output_dir / "sess1.jsonl").exists()
        assert (output_dir / "sess2.jsonl").exists()
        assert (output_dir / "sess3.jsonl").exists()


class TestExportEmptySession:
    """Test exporting session with no events."""

    def test_export_empty_session(self, tmp_path):
        """Test exporting empty session creates empty file."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        store = EventStore(db_path)
        # Don't add any events
        count = export_session_jsonl(store, "empty_session", output_path)
        store.close()

        assert count == 0
        assert output_path.exists()
        assert output_path.read_text() == ""


# =============================================================================
# Section 2: JSONL Import Functionality (8 tests)
# =============================================================================

class TestImportSessionJsonl:
    """Test importing session from JSONL file."""

    def test_import_session_jsonl(self, tmp_path):
        """Test importing valid JSONL file."""
        db_path = tmp_path / "pathway.db"
        input_path = tmp_path / "events.jsonl"

        # Create JSONL file
        events = []
        for i in range(5):
            events.append({
                "event_id": f"e{i:03d}",
                "session_id": "test_session",
                "seq": i,
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": "IntentCreated",
                "head_id": "main",
                "actor": {"kind": "system"},
                "payload": {"goal": "test"},
            })
        input_path.write_text("\n".join(json.dumps(e) for e in events))

        store = EventStore(db_path)
        count = import_session_jsonl(store, input_path)

        assert count == 5
        assert store.session_exists("test_session")
        store.close()


class TestImportWithSessionOverride:
    """Test session_id_override replaces IDs."""

    def test_import_with_session_override(self, tmp_path):
        """Test session_id_override replaces all session IDs."""
        db_path = tmp_path / "pathway.db"
        input_path = tmp_path / "events.jsonl"

        event = {
            "event_id": "e001",
            "session_id": "original_session",
            "seq": 0,
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "IntentCreated",
            "head_id": "main",
            "actor": {"kind": "system"},
            "payload": {"goal": "test"},
        }
        input_path.write_text(json.dumps(event))

        store = EventStore(db_path)
        import_session_jsonl(store, input_path, session_id_override="new_session")

        assert store.session_exists("new_session")
        assert not store.session_exists("original_session")
        store.close()


class TestImportInvalidJson:
    """Test import handles invalid JSON gracefully."""

    def test_import_invalid_json(self, tmp_path):
        """Test import raises error on invalid JSON."""
        db_path = tmp_path / "pathway.db"
        input_path = tmp_path / "invalid.jsonl"

        input_path.write_text("not valid json\n")

        store = EventStore(db_path)
        with pytest.raises(ValueError, match="Invalid JSON"):
            import_session_jsonl(store, input_path)
        store.close()


class TestImportMissingFields:
    """Test import handles incomplete events."""

    def test_import_missing_fields(self, tmp_path):
        """Test import raises error on incomplete events."""
        db_path = tmp_path / "pathway.db"
        input_path = tmp_path / "incomplete.jsonl"

        # Missing required fields
        input_path.write_text('{"event_id": "e001"}\n')

        store = EventStore(db_path)
        with pytest.raises(ValueError, match="Invalid event"):
            import_session_jsonl(store, input_path)
        store.close()


class TestImportEmptyFile:
    """Test import handles empty file."""

    def test_import_empty_file(self, tmp_path):
        """Test import handles empty JSONL file."""
        db_path = tmp_path / "pathway.db"
        input_path = tmp_path / "empty.jsonl"

        input_path.write_text("")

        store = EventStore(db_path)
        count = import_session_jsonl(store, input_path)

        assert count == 0
        store.close()


class TestImportLargeFile:
    """Test import handles large JSONL files."""

    def test_import_large_file(self, tmp_path):
        """Test import processes large files efficiently."""
        db_path = tmp_path / "pathway.db"
        input_path = tmp_path / "large.jsonl"

        # Create 1000 events
        events = []
        for i in range(1000):
            events.append({
                "event_id": f"e{i:04d}",
                "session_id": "test_session",
                "seq": i,
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": "IntentCreated",
                "head_id": "main",
                "actor": {"kind": "system"},
                "payload": {"goal": f"test {i}"},
            })
        input_path.write_text("\n".join(json.dumps(e) for e in events))

        store = EventStore(db_path)
        count = import_session_jsonl(store, input_path)

        assert count == 1000
        store.close()


class TestImportAllJsonlFiles:
    """Test importing all JSONL files from directory."""

    def test_import_all_jsonl_files(self, tmp_path):
        """Test importing all JSONL files from directory."""
        db_path = tmp_path / "pathway.db"
        input_dir = tmp_path / "imports"
        input_dir.mkdir()

        # Create multiple JSONL files
        for sess in ["sess1", "sess2"]:
            events = []
            for i in range(3):
                events.append({
                    "event_id": f"{sess}_e{i}",
                    "session_id": sess,
                    "seq": i,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "type": "IntentCreated",
                    "head_id": "main",
                    "actor": {"kind": "system"},
                    "payload": {"goal": "test"},
                })
            (input_dir / f"{sess}.jsonl").write_text("\n".join(json.dumps(e) for e in events))

        store = EventStore(db_path)
        results = import_all_jsonl_files(store, input_dir)

        assert len(results) == 2
        assert store.session_exists("sess1")
        assert store.session_exists("sess2")
        store.close()


class TestExportImportRoundtrip:
    """Test export then import yields same data."""

    def test_export_import_roundtrip(self, tmp_path):
        """Test data survives export/import cycle."""
        db_path = tmp_path / "original.db"
        export_path = tmp_path / "exported.jsonl"
        new_db_path = tmp_path / "imported.db"

        # Create original data
        original_store = EventStore(db_path)
        for i in range(10):
            original_store.append(make_test_event(
                f"e{i:03d}", seq=i,
                payload={"goal": f"test goal {i}", "data": {"nested": True}},
            ))
        original_events = original_store.get_events("test_session")

        # Export
        export_session_jsonl(original_store, "test_session", export_path)
        original_store.close()

        # Import to new database
        new_store = EventStore(new_db_path)
        import_session_jsonl(new_store, export_path)
        imported_events = new_store.get_events("test_session")
        new_store.close()

        # Verify
        assert len(imported_events) == len(original_events)
        for orig, imp in zip(original_events, imported_events):
            assert orig.event_id == imp.event_id
            assert orig.seq == imp.seq
            assert orig.payload == imp.payload


# =============================================================================
# Section 3: Store Concurrency & Edge Cases (10 tests)
# =============================================================================

class TestConcurrentAutoSeqSafety:
    """Test auto_seq is thread-safe."""

    def test_concurrent_auto_seq(self, tmp_path):
        """Test concurrent appends with auto_seq are unique."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        seqs = []
        lock = threading.Lock()

        def append_event(i):
            event = make_test_event(f"e{i:04d}", seq=0)  # seq will be auto-assigned
            result = store.append(event, auto_seq=True)
            with lock:
                seqs.append(result.seq)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(append_event, i) for i in range(100)]
            for f in futures:
                f.result()

        store.close()

        # All seqs should be unique
        assert len(seqs) == len(set(seqs))


class TestEventIdCaseSensitive:
    """Test event_id is case-sensitive."""

    def test_event_id_case_sensitive(self, tmp_path):
        """Test event_id 'ABC' and 'abc' are different."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        store.append(make_test_event("ABC", seq=0))
        store.append(make_test_event("abc", seq=1))

        assert store.get_event("ABC") is not None
        assert store.get_event("abc") is not None
        assert store.get_event("ABC").event_id != store.get_event("abc").event_id

        store.close()


class TestSessionIdCaseSensitive:
    """Test session_id is case-sensitive."""

    def test_session_id_case_sensitive(self, tmp_path):
        """Test session_id 'Session1' and 'session1' are different."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        store.append(make_test_event("e001", session_id="Session1", seq=0))
        store.append(make_test_event("e002", session_id="session1", seq=0))

        sessions = store.list_sessions()
        assert "Session1" in sessions
        assert "session1" in sessions

        store.close()


class TestHeadIdSpecialCharacters:
    """Test head_id with special chars."""

    def test_head_id_special_characters(self, tmp_path):
        """Test head_id 'feature/my-branch' works."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        store.append(make_test_event("e001", seq=0, head_id="feature/my-branch"))
        store.append(make_test_event("e002", seq=1, head_id="fix_bug-123"))

        heads = store.get_all_heads("test_session")
        assert "feature/my-branch" in heads
        assert "fix_bug-123" in heads

        store.close()


class TestEmptyPayload:
    """Test event with minimal payload."""

    def test_empty_payload(self, tmp_path):
        """Test event with minimal payload works (store level, not validation)."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # IntentCreated requires 'goal', use minimal valid payload
        store.append(make_test_event("e001", seq=0, payload={"goal": ""}))

        event = store.get_event("e001")
        assert event.payload == {"goal": ""}

        store.close()


class TestLargePayload:
    """Test event with large payload."""

    def test_large_payload(self, tmp_path):
        """Test event with 100KB payload stores correctly."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        # Create ~100KB payload
        large_data = {"data": "x" * 100000}
        store.append(make_test_event("e001", seq=0, payload=large_data))

        event = store.get_event("e001")
        assert len(event.payload["data"]) == 100000

        store.close()


class TestUnicodeInPayload:
    """Test payload with unicode."""

    def test_unicode_in_payload(self, tmp_path):
        """Test payload with emoji and foreign characters."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        unicode_payload = {
            "emoji": "🎯🚀💻",
            "japanese": "日本語テスト",
            "arabic": "اختبار",
            "special": "Test with 'quotes' and \"double quotes\"",
        }
        store.append(make_test_event("e001", seq=0, payload=unicode_payload))

        event = store.get_event("e001")
        assert event.payload["emoji"] == "🎯🚀💻"
        assert event.payload["japanese"] == "日本語テスト"

        store.close()


class TestGetEventsLimitOffset:
    """Test pagination with limit/offset (if supported)."""

    def test_get_events_seq_range(self, tmp_path):
        """Test get_events with from_seq and to_seq."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        for i in range(20):
            store.append(make_test_event(f"e{i:03d}", seq=i))

        # Get events 5-10
        events = store.get_events("test_session", from_seq=5, to_seq=10)
        assert len(events) == 6  # 5, 6, 7, 8, 9, 10
        assert events[0].seq == 5
        assert events[-1].seq == 10

        store.close()


class TestDuplicateEventIdFails:
    """Test duplicate event_id is rejected."""

    def test_duplicate_event_id_fails(self, tmp_path):
        """Test duplicate event_id raises error."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        store.append(make_test_event("e001", seq=0))

        with pytest.raises(ValueError):
            store.append(make_test_event("e001", seq=1))

        store.close()


class TestDuplicateSeqFails:
    """Test duplicate seq in same session is rejected."""

    def test_duplicate_seq_fails(self, tmp_path):
        """Test duplicate seq in same session raises error."""
        db_path = tmp_path / "pathway.db"
        store = EventStore(db_path)

        store.append(make_test_event("e001", seq=0))

        with pytest.raises(ValueError):
            store.append(make_test_event("e002", seq=0))  # Same seq

        store.close()
