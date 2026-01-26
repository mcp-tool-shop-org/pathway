"""SQLite-based append-only event store for Pathway.

Design principles:
- Events are never edited or deleted
- seq is strictly increasing per session
- Indexes support efficient queries for derived views
- Thread-safe for concurrent reads and writes
"""

import json
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path

from pathway.models.events import EventEnvelope, Actor, EventType


class EventStore:
    """Append-only event store backed by SQLite.

    Thread-safe: uses per-thread connections for concurrent access.
    For in-memory databases, uses a unique shared cache URI to allow multi-threaded access
    while keeping each store instance isolated.
    """

    def __init__(self, db_path: str | Path = ":memory:"):
        """Initialize the store.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory.
        """
        self._original_path = str(db_path)

        # For in-memory DBs, use unique shared cache for multi-thread access
        # Each store instance gets its own in-memory DB
        if self._original_path == ":memory:":
            unique_id = uuid.uuid4().hex[:8]
            self.db_path = f"file:pathway_{unique_id}?mode=memory&cache=shared"
            self._uri = True
        else:
            self.db_path = self._original_path
            self._uri = False

        self._local = threading.local()
        self._write_lock = threading.Lock()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create a thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                uri=self._uri,
                check_same_thread=False,
                timeout=30.0,
            )
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent access (file-based only)
            if not self._uri:
                self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _init_schema(self) -> None:
        """Create tables and indexes if they don't exist."""
        conn = self._get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                head_id TEXT NOT NULL,
                parent_event_id TEXT,
                ts TEXT NOT NULL,
                type TEXT NOT NULL,
                waypoint_id TEXT,
                trail_version_id TEXT,
                actor_kind TEXT NOT NULL,
                actor_id TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_session_seq
                ON events(session_id, seq);

            CREATE INDEX IF NOT EXISTS idx_session_head_seq
                ON events(session_id, head_id, seq);

            CREATE INDEX IF NOT EXISTS idx_session_parent
                ON events(session_id, parent_event_id);

            CREATE INDEX IF NOT EXISTS idx_session_type
                ON events(session_id, type);
            """
        )
        conn.commit()

    def append(self, event: EventEnvelope, auto_seq: bool = False) -> EventEnvelope:
        """Append an event to the store.

        Args:
            event: The event to append.
            auto_seq: If True, atomically assign the next seq number.
                     The event.seq value will be ignored.

        Returns:
            The event with seq populated.

        Raises:
            ValueError: If event_id is missing or seq already exists.
        """
        # Use write lock for thread-safe concurrent writes
        with self._write_lock:
            conn = self._get_conn()

            if auto_seq:
                # Atomic seq assignment using INSERT with subquery
                # Combined with write_lock for full thread safety
                try:
                    cursor = conn.execute(
                        """
                        INSERT INTO events (
                            event_id, session_id, seq, head_id, parent_event_id,
                            ts, type, waypoint_id, trail_version_id,
                            actor_kind, actor_id, payload_json
                        ) VALUES (
                            ?, ?,
                            COALESCE((SELECT MAX(seq) + 1 FROM events WHERE session_id = ?), 0),
                            ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                        RETURNING seq
                        """,
                        (
                            event.event_id,
                            event.session_id,
                            event.session_id,  # For the subquery
                            event.head_id,
                            event.parent_event_id,
                            event.ts.isoformat(),
                            event.type.value,
                            event.waypoint_id,
                            event.trail_version_id,
                            event.actor.kind.value,
                            event.actor.id,
                            json.dumps(event.payload),
                        ),
                    )
                    assigned_seq = cursor.fetchone()[0]
                    conn.commit()
                    return event.model_copy(update={"seq": assigned_seq})
                except sqlite3.IntegrityError as e:
                    raise ValueError(f"Event already exists or constraint violation: {e}") from e

            # Explicit seq provided
            try:
                conn.execute(
                    """
                    INSERT INTO events (
                        event_id, session_id, seq, head_id, parent_event_id,
                        ts, type, waypoint_id, trail_version_id,
                        actor_kind, actor_id, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.session_id,
                        event.seq,
                        event.head_id,
                        event.parent_event_id,
                        event.ts.isoformat(),
                        event.type.value,
                        event.waypoint_id,
                        event.trail_version_id,
                        event.actor.kind.value,
                        event.actor.id,
                        json.dumps(event.payload),
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                raise ValueError(f"Event already exists or seq conflict: {e}") from e

            return event

    def get_events(
        self,
        session_id: str,
        head_id: str | None = None,
        from_seq: int | None = None,
        to_seq: int | None = None,
        event_type: EventType | None = None,
    ) -> list[EventEnvelope]:
        """Get events for a session with optional filters.

        Args:
            session_id: The session to query.
            head_id: Filter by branch (optional).
            from_seq: Start from this seq (inclusive, optional).
            to_seq: End at this seq (inclusive, optional).
            event_type: Filter by event type (optional).

        Returns:
            List of events ordered by seq.
        """
        conn = self._get_conn()

        query = "SELECT * FROM events WHERE session_id = ?"
        params: list = [session_id]

        if head_id is not None:
            query += " AND head_id = ?"
            params.append(head_id)

        if from_seq is not None:
            query += " AND seq >= ?"
            params.append(from_seq)

        if to_seq is not None:
            query += " AND seq <= ?"
            params.append(to_seq)

        if event_type is not None:
            query += " AND type = ?"
            params.append(event_type.value)

        query += " ORDER BY seq"

        cursor = conn.execute(query, params)
        return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_event(self, event_id: str) -> EventEnvelope | None:
        """Get a single event by ID.

        Args:
            event_id: The event ID to look up.

        Returns:
            The event, or None if not found.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM events WHERE event_id = ?", (event_id,)
        )
        row = cursor.fetchone()
        return self._row_to_event(row) if row else None

    def get_children(self, parent_event_id: str) -> list[EventEnvelope]:
        """Get all events that have this event as their parent.

        Args:
            parent_event_id: The parent event ID.

        Returns:
            List of child events.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM events WHERE parent_event_id = ? ORDER BY seq",
            (parent_event_id,),
        )
        return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_latest_seq(self, session_id: str) -> int:
        """Get the latest sequence number for a session.

        Args:
            session_id: The session to query.

        Returns:
            The latest seq, or -1 if no events exist.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT MAX(seq) FROM events WHERE session_id = ?", (session_id,)
        )
        result = cursor.fetchone()[0]
        return result if result is not None else -1

    def get_next_seq(self, session_id: str) -> int:
        """Get the next sequence number for a session.

        Args:
            session_id: The session to query.

        Returns:
            The next seq (latest + 1, or 0 if no events).
        """
        return self.get_latest_seq(session_id) + 1

    def get_all_heads(self, session_id: str) -> list[str]:
        """Get all unique head_ids for a session.

        Args:
            session_id: The session to query.

        Returns:
            List of unique head_ids.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT DISTINCT head_id FROM events WHERE session_id = ?",
            (session_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    def get_head_tip(self, session_id: str, head_id: str) -> EventEnvelope | None:
        """Get the latest event on a specific head.

        Args:
            session_id: The session to query.
            head_id: The branch to query.

        Returns:
            The latest event on that head, or None if empty.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT * FROM events
            WHERE session_id = ? AND head_id = ?
            ORDER BY seq DESC LIMIT 1
            """,
            (session_id, head_id),
        )
        row = cursor.fetchone()
        return self._row_to_event(row) if row else None

    def get_active_head(self, session_id: str) -> str:
        """Get the currently active head (head_id of latest event by seq).

        Args:
            session_id: The session to query.

        Returns:
            The active head_id, or "main" if no events.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT head_id FROM events
            WHERE session_id = ?
            ORDER BY seq DESC LIMIT 1
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else "main"

    def session_exists(self, session_id: str) -> bool:
        """Check if a session has any events.

        Args:
            session_id: The session to check.

        Returns:
            True if session has at least one event.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT 1 FROM events WHERE session_id = ? LIMIT 1", (session_id,)
        )
        return cursor.fetchone() is not None

    def list_sessions(self) -> list[str]:
        """List all session IDs in the store.

        Returns:
            List of unique session_ids.
        """
        conn = self._get_conn()
        cursor = conn.execute("SELECT DISTINCT session_id FROM events")
        return [row[0] for row in cursor.fetchall()]

    def close(self) -> None:
        """Close the thread-local database connection."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    def _row_to_event(self, row: sqlite3.Row) -> EventEnvelope:
        """Convert a database row to an EventEnvelope."""
        return EventEnvelope(
            event_id=row["event_id"],
            session_id=row["session_id"],
            seq=row["seq"],
            head_id=row["head_id"],
            parent_event_id=row["parent_event_id"],
            ts=datetime.fromisoformat(row["ts"]),
            type=EventType(row["type"]),
            waypoint_id=row["waypoint_id"],
            trail_version_id=row["trail_version_id"],
            actor=Actor(kind=row["actor_kind"], id=row["actor_id"]),
            payload=json.loads(row["payload_json"]),
        )

    def __enter__(self) -> "EventStore":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
