"""JSONL import/export for Pathway event stores.

Used for debugging, sharing repros, and migrating data.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pathway.models.events import EventEnvelope, Actor, EventType

if TYPE_CHECKING:
    from pathway.store.sqlite_store import EventStore


def export_session_jsonl(
    store: "EventStore",
    session_id: str,
    output_path: str | Path,
) -> int:
    """Export a session to a JSONL file.

    Each line is a JSON object representing one event.

    Args:
        store: The event store to read from.
        session_id: The session to export.
        output_path: Path to write the JSONL file.

    Returns:
        Number of events exported.
    """
    events = store.get_events(session_id)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for event in events:
            # Convert to dict with ISO timestamp
            event_dict = event.model_dump()
            event_dict["ts"] = event.ts.isoformat()
            event_dict["type"] = event.type.value
            event_dict["actor"]["kind"] = event.actor.kind.value
            f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")

    return len(events)


def import_session_jsonl(
    store: "EventStore",
    input_path: str | Path,
    session_id_override: str | None = None,
) -> int:
    """Import events from a JSONL file into the store.

    Args:
        store: The event store to write to.
        input_path: Path to the JSONL file.
        session_id_override: If provided, replace all session_ids with this.

    Returns:
        Number of events imported.

    Raises:
        ValueError: If the file contains invalid events.
    """
    input_path = Path(input_path)
    count = 0

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num}: {e}") from e

            # Parse the event
            try:
                # Handle timestamp
                if isinstance(data.get("ts"), str):
                    data["ts"] = datetime.fromisoformat(data["ts"])

                # Handle enum values
                if isinstance(data.get("type"), str):
                    data["type"] = EventType(data["type"])

                # Handle actor
                if isinstance(data.get("actor"), dict):
                    data["actor"] = Actor(**data["actor"])

                # Override session_id if requested
                if session_id_override:
                    data["session_id"] = session_id_override

                event = EventEnvelope(**data)
                store.append(event)
                count += 1

            except Exception as e:
                raise ValueError(f"Invalid event on line {line_num}: {e}") from e

    return count


def export_all_sessions_jsonl(
    store: "EventStore",
    output_dir: str | Path,
) -> dict[str, int]:
    """Export all sessions to separate JSONL files.

    Args:
        store: The event store to read from.
        output_dir: Directory to write files to.

    Returns:
        Dict mapping session_id to event count.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for session_id in store.list_sessions():
        output_path = output_dir / f"{session_id}.jsonl"
        count = export_session_jsonl(store, session_id, output_path)
        results[session_id] = count

    return results


def import_all_jsonl_files(
    store: "EventStore",
    input_dir: str | Path,
) -> dict[str, int]:
    """Import all JSONL files from a directory.

    Args:
        store: The event store to write to.
        input_dir: Directory containing JSONL files.

    Returns:
        Dict mapping filename to event count.
    """
    input_dir = Path(input_dir)
    results = {}

    for path in input_dir.glob("*.jsonl"):
        count = import_session_jsonl(store, path)
        results[path.name] = count

    return results
