"""
Batch 1: CLI tests - Init, Import, Export commands (25 tests)
Tests for pathway init, import, and export CLI commands.
"""

import json
import subprocess
import sys
import pytest
from pathlib import Path
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

from pathway.cli import cmd_init, cmd_import, cmd_export, main
from pathway.store.sqlite_store import EventStore
from pathway.models.events import EventEnvelope, EventType, Actor, ActorKind


# =============================================================================
# Helpers
# =============================================================================

def make_test_event(
    event_id: str,
    session_id: str = "test_session",
    seq: int = 0,
    event_type: EventType = EventType.INTENT_CREATED,
    payload: dict = None,
) -> EventEnvelope:
    """Create a test event."""
    return EventEnvelope(
        event_id=event_id,
        session_id=session_id,
        seq=seq,
        ts=datetime.now(timezone.utc),
        type=event_type,
        head_id="main",
        actor=Actor(kind=ActorKind.SYSTEM),
        payload=payload or {"goal": "test"},
    )


def create_jsonl_file(path: Path, events: list[dict]) -> None:
    """Create a JSONL file with the given events."""
    with open(path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def make_event_dict(
    event_id: str,
    session_id: str = "test_session",
    seq: int = 0,
    event_type: str = "IntentCreated",
) -> dict:
    """Create an event dictionary for JSONL."""
    return {
        "event_id": event_id,
        "session_id": session_id,
        "seq": seq,
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "head_id": "main",
        "actor": {"kind": "system"},
        "payload": {"goal": "test goal"},
    }


class MockArgs:
    """Mock argparse namespace for testing."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# =============================================================================
# Section 1: Init Command (5 tests)
# =============================================================================

class TestCmdInitCreatesDatabase:
    """Test init command creates new database."""

    def test_init_creates_database(self, tmp_path):
        """Test init command creates new database."""
        db_path = tmp_path / "pathway.db"
        args = MockArgs(db=str(db_path), force=False)

        result = cmd_init(args)

        assert result == 0
        assert db_path.exists()


class TestCmdInitNoOverwrite:
    """Test init refuses to overwrite existing database."""

    def test_init_no_overwrite(self, tmp_path, capsys):
        """Test init refuses to overwrite existing database without --force."""
        db_path = tmp_path / "pathway.db"
        db_path.touch()  # Create existing file

        args = MockArgs(db=str(db_path), force=False)
        result = cmd_init(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "already exists" in captured.out


class TestCmdInitForceOverwrites:
    """Test --force flag overwrites existing database."""

    def test_init_force_overwrites(self, tmp_path):
        """Test --force flag overwrites existing database."""
        db_path = tmp_path / "pathway.db"
        db_path.write_text("old content")

        args = MockArgs(db=str(db_path), force=True)
        result = cmd_init(args)

        assert result == 0
        # Should be a valid SQLite database now
        store = EventStore(db_path)
        store.close()


class TestCmdInitCustomPath:
    """Test init with custom database path."""

    def test_init_custom_path(self, tmp_path):
        """Test init with custom database path in existing directory."""
        custom_path = tmp_path / "custom.db"
        args = MockArgs(db=str(custom_path), force=False)

        result = cmd_init(args)

        assert result == 0
        assert custom_path.exists()


class TestCmdInitInitializesSchema:
    """Test init creates proper schema."""

    def test_init_initializes_schema(self, tmp_path):
        """Test init creates database with proper schema."""
        db_path = tmp_path / "pathway.db"
        args = MockArgs(db=str(db_path), force=False)

        cmd_init(args)

        # Verify schema by using the store
        store = EventStore(db_path)
        # Should be able to list sessions (empty)
        sessions = store.list_sessions()
        assert sessions == []
        store.close()


# =============================================================================
# Section 2: Import Command (10 tests)
# =============================================================================

class TestCmdImportJsonl:
    """Test importing events from JSONL file."""

    def test_import_jsonl(self, tmp_path, capsys):
        """Test importing events from JSONL file."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "events.jsonl"

        # Create JSONL file
        events = [make_event_dict(f"e{i:03d}", seq=i) for i in range(5)]
        create_jsonl_file(jsonl_path, events)

        # Initialize and import
        EventStore(db_path).close()
        args = MockArgs(db=str(db_path), input=str(jsonl_path), session_id=None)
        result = cmd_import(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Imported 5 events" in captured.out


class TestCmdImportWithSessionOverride:
    """Test --session-id overrides JSONL session IDs."""

    def test_import_with_session_override(self, tmp_path):
        """Test --session-id overrides JSONL session IDs."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "events.jsonl"

        # Create JSONL with original session_id
        events = [make_event_dict("e001", session_id="original_sess", seq=0)]
        create_jsonl_file(jsonl_path, events)

        EventStore(db_path).close()
        args = MockArgs(db=str(db_path), input=str(jsonl_path), session_id="new_sess")
        cmd_import(args)

        # Verify session_id was overridden
        store = EventStore(db_path)
        assert store.session_exists("new_sess")
        assert not store.session_exists("original_sess")
        store.close()


class TestCmdImportFileNotFound:
    """Test import with missing file."""

    def test_import_file_not_found(self, tmp_path, capsys):
        """Test import with missing file errors gracefully."""
        db_path = tmp_path / "pathway.db"
        EventStore(db_path).close()

        args = MockArgs(
            db=str(db_path),
            input=str(tmp_path / "nonexistent.jsonl"),
            session_id=None,
        )
        result = cmd_import(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestCmdImportInvalidJsonl:
    """Test import with malformed JSONL."""

    def test_import_invalid_jsonl(self, tmp_path, capsys):
        """Test import with malformed JSONL errors with clear message."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "invalid.jsonl"

        # Create invalid JSONL
        jsonl_path.write_text("not valid json\n")

        EventStore(db_path).close()
        args = MockArgs(db=str(db_path), input=str(jsonl_path), session_id=None)
        result = cmd_import(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.out.lower() or "Invalid" in captured.out


class TestCmdImportEmptyFile:
    """Test import with empty JSONL file."""

    def test_import_empty_file(self, tmp_path, capsys):
        """Test import with empty JSONL file succeeds with 0 imports."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "empty.jsonl"

        jsonl_path.write_text("")

        EventStore(db_path).close()
        args = MockArgs(db=str(db_path), input=str(jsonl_path), session_id=None)
        result = cmd_import(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Imported 0 events" in captured.out


class TestCmdImportMissingRequiredFields:
    """Test import with incomplete events."""

    def test_import_missing_required_fields(self, tmp_path, capsys):
        """Test import handles incomplete events with error."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "incomplete.jsonl"

        # Create JSONL with missing required field
        jsonl_path.write_text('{"event_id": "e001"}\n')

        EventStore(db_path).close()
        args = MockArgs(db=str(db_path), input=str(jsonl_path), session_id=None)
        result = cmd_import(args)

        assert result == 1


class TestCmdImportMultipleSessions:
    """Test import preserves multiple session IDs."""

    def test_import_multiple_sessions(self, tmp_path):
        """Test import preserves multiple session IDs from file."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "events.jsonl"

        events = [
            make_event_dict("e001", session_id="sess1", seq=0),
            make_event_dict("e002", session_id="sess2", seq=0),
            make_event_dict("e003", session_id="sess1", seq=1),
        ]
        create_jsonl_file(jsonl_path, events)

        EventStore(db_path).close()
        args = MockArgs(db=str(db_path), input=str(jsonl_path), session_id=None)
        cmd_import(args)

        store = EventStore(db_path)
        assert store.session_exists("sess1")
        assert store.session_exists("sess2")
        store.close()


class TestCmdImportLargeFile:
    """Test import handles large JSONL files."""

    def test_import_large_file(self, tmp_path, capsys):
        """Test import handles large JSONL files efficiently."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "large.jsonl"

        # Create 1000 events
        events = [make_event_dict(f"e{i:04d}", seq=i) for i in range(1000)]
        create_jsonl_file(jsonl_path, events)

        EventStore(db_path).close()
        args = MockArgs(db=str(db_path), input=str(jsonl_path), session_id=None)
        result = cmd_import(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Imported 1000 events" in captured.out


class TestCmdImportUnicodeContent:
    """Test import handles unicode in payloads."""

    def test_import_unicode_content(self, tmp_path):
        """Test import handles unicode in payloads correctly."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "unicode.jsonl"

        event = make_event_dict("e001", seq=0)
        event["payload"] = {"goal": "Test émojis: 🎯 and 日本語"}
        create_jsonl_file(jsonl_path, [event])

        EventStore(db_path).close()
        args = MockArgs(db=str(db_path), input=str(jsonl_path), session_id=None)
        result = cmd_import(args)

        assert result == 0

        # Verify unicode preserved
        store = EventStore(db_path)
        events = store.get_events("test_session")
        assert "🎯" in str(events[0].payload)
        store.close()


class TestCmdImportDuplicateEventIds:
    """Test import detects duplicate event_ids."""

    def test_import_duplicate_event_ids(self, tmp_path, capsys):
        """Test import detects duplicate event_ids."""
        db_path = tmp_path / "pathway.db"
        jsonl_path = tmp_path / "dupes.jsonl"

        # Create JSONL with duplicate event_id
        events = [
            make_event_dict("e001", seq=0),
            make_event_dict("e001", seq=1),  # Same event_id
        ]
        create_jsonl_file(jsonl_path, events)

        EventStore(db_path).close()
        args = MockArgs(db=str(db_path), input=str(jsonl_path), session_id=None)
        result = cmd_import(args)

        # Should fail due to duplicate event_id
        assert result == 1


# =============================================================================
# Section 3: Export Command (10 tests)
# =============================================================================

class TestCmdExportSession:
    """Test exporting session to JSONL."""

    def test_export_session(self, tmp_path, capsys):
        """Test exporting session to JSONL."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        # Create session with events
        store = EventStore(db_path)
        for i in range(3):
            store.append(make_test_event(f"e{i:03d}", seq=i))
        store.close()

        args = MockArgs(
            db=str(db_path),
            session_id="test_session",
            output=str(output_path),
        )
        result = cmd_export(args)

        assert result == 0
        assert output_path.exists()
        captured = capsys.readouterr()
        assert "Exported 3 events" in captured.out


class TestCmdExportSessionNotFound:
    """Test export with non-existent session."""

    def test_export_session_not_found(self, tmp_path, capsys):
        """Test export with non-existent session errors."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        EventStore(db_path).close()

        args = MockArgs(
            db=str(db_path),
            session_id="nonexistent",
            output=str(output_path),
        )
        result = cmd_export(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestCmdExportOverwritesExisting:
    """Test export overwrites existing file."""

    def test_export_overwrites_existing(self, tmp_path):
        """Test export overwrites existing file."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        # Create existing file
        output_path.write_text("old content")

        store = EventStore(db_path)
        store.append(make_test_event("e001", seq=0))
        store.close()

        args = MockArgs(
            db=str(db_path),
            session_id="test_session",
            output=str(output_path),
        )
        cmd_export(args)

        # Should be overwritten with new content
        content = output_path.read_text()
        assert "e001" in content
        assert "old content" not in content


class TestCmdExportCustomOutputPath:
    """Test export to custom path."""

    def test_export_custom_output_path(self, tmp_path):
        """Test export to custom path including nested directories."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "subdir" / "nested" / "output.jsonl"

        store = EventStore(db_path)
        store.append(make_test_event("e001", seq=0))
        store.close()

        args = MockArgs(
            db=str(db_path),
            session_id="test_session",
            output=str(output_path),
        )
        result = cmd_export(args)

        assert result == 0
        assert output_path.exists()


class TestCmdExportPreservesOrder:
    """Test events are exported in seq order."""

    def test_export_preserves_order(self, tmp_path):
        """Test events are exported in seq order."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        store = EventStore(db_path)
        # Insert out of order
        store.append(make_test_event("e003", seq=2))
        store.append(make_test_event("e001", seq=0))
        store.append(make_test_event("e002", seq=1))
        store.close()

        args = MockArgs(
            db=str(db_path),
            session_id="test_session",
            output=str(output_path),
        )
        cmd_export(args)

        # Read and verify order
        lines = output_path.read_text().strip().split("\n")
        event_ids = [json.loads(line)["event_id"] for line in lines]
        assert event_ids == ["e001", "e002", "e003"]


class TestCmdExportPreservesAllFields:
    """Test all event fields are preserved."""

    def test_export_preserves_all_fields(self, tmp_path):
        """Test all event fields are preserved in export."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        store = EventStore(db_path)
        event = make_test_event("e001", seq=0)
        store.append(event)
        store.close()

        args = MockArgs(
            db=str(db_path),
            session_id="test_session",
            output=str(output_path),
        )
        cmd_export(args)

        # Verify all fields present
        line = output_path.read_text().strip()
        data = json.loads(line)
        assert "event_id" in data
        assert "session_id" in data
        assert "seq" in data
        assert "ts" in data
        assert "type" in data
        assert "head_id" in data
        assert "actor" in data
        assert "payload" in data


class TestCmdExportEmptySession:
    """Test exporting session with no events."""

    def test_export_empty_session(self, tmp_path, capsys):
        """Test exporting session with no events."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        # Create empty database with no events
        store = EventStore(db_path)
        store.close()

        args = MockArgs(
            db=str(db_path),
            session_id="empty_session",
            output=str(output_path),
        )
        result = cmd_export(args)

        # Session doesn't exist, should error
        assert result == 1


class TestCmdExportJsonlFormat:
    """Test exported file is valid JSONL."""

    def test_export_valid_jsonl(self, tmp_path):
        """Test exported file is valid JSONL format."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        store = EventStore(db_path)
        for i in range(3):
            store.append(make_test_event(f"e{i:03d}", seq=i))
        store.close()

        args = MockArgs(
            db=str(db_path),
            session_id="test_session",
            output=str(output_path),
        )
        cmd_export(args)

        # Each line should be valid JSON
        with open(output_path) as f:
            for line in f:
                json.loads(line)  # Should not raise


class TestCmdExportRoundtrip:
    """Test export then import yields same data."""

    def test_export_import_roundtrip(self, tmp_path):
        """Test export then import yields same data."""
        db_path = tmp_path / "original.db"
        export_path = tmp_path / "exported.jsonl"
        new_db_path = tmp_path / "imported.db"

        # Create original session
        store = EventStore(db_path)
        for i in range(5):
            store.append(make_test_event(f"e{i:03d}", seq=i))
        original_events = store.get_events("test_session")
        store.close()

        # Export
        args = MockArgs(
            db=str(db_path),
            session_id="test_session",
            output=str(export_path),
        )
        cmd_export(args)

        # Import to new db
        EventStore(new_db_path).close()
        args = MockArgs(
            db=str(new_db_path),
            input=str(export_path),
            session_id=None,
        )
        cmd_import(args)

        # Verify same data
        store = EventStore(new_db_path)
        imported_events = store.get_events("test_session")
        store.close()

        assert len(imported_events) == len(original_events)
        for orig, imp in zip(original_events, imported_events):
            assert orig.event_id == imp.event_id
            assert orig.seq == imp.seq


class TestCmdExportMultipleHeads:
    """Test export includes events from all heads."""

    def test_export_multiple_heads(self, tmp_path):
        """Test export includes events from all heads/branches."""
        db_path = tmp_path / "pathway.db"
        output_path = tmp_path / "output.jsonl"

        store = EventStore(db_path)
        store.append(make_test_event("e001", seq=0))
        # Create event on different head
        event2 = EventEnvelope(
            event_id="e002",
            session_id="test_session",
            seq=1,
            ts=datetime.now(timezone.utc),
            type=EventType.INTENT_CREATED,
            head_id="branch1",  # Different head
            actor=Actor(kind=ActorKind.SYSTEM),
            payload={"goal": "test"},
        )
        store.append(event2)
        store.close()

        args = MockArgs(
            db=str(db_path),
            session_id="test_session",
            output=str(output_path),
        )
        cmd_export(args)

        # Should export both events
        lines = output_path.read_text().strip().split("\n")
        assert len(lines) == 2
