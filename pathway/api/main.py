"""FastAPI application for Pathway.

Endpoints:
- POST /events: Append an event
- GET /session/{session_id}/state: Get derived state
- GET /session/{session_id}/events: Get raw events
- GET /sessions: List all sessions

Security:
- Set PATHWAY_API_KEY env var to require authentication
- Payload size limited to 1MB by default
- Session IDs validated (alphanumeric + underscore/hyphen, max 128 chars)
"""

import os
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ulid
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, field_validator


# -----------------------------------------------------------------------------
# Security configuration
# -----------------------------------------------------------------------------

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
MAX_PAYLOAD_SIZE = int(os.environ.get("PATHWAY_MAX_PAYLOAD_SIZE", 1024 * 1024))  # 1MB default
SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")

from pathway.models.events import EventEnvelope, EventType, Actor, ActorKind
from pathway.models.derived import SessionState
from pathway.store.sqlite_store import EventStore
from pathway.reducers.session import reduce_session_state


# -----------------------------------------------------------------------------
# Request/Response models
# -----------------------------------------------------------------------------


def validate_session_id(session_id: str) -> str:
    """Validate session_id format to prevent injection attacks."""
    if not SESSION_ID_PATTERN.match(session_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id: must be 1-128 alphanumeric characters, underscores, or hyphens",
        )
    return session_id


class EventRequest(BaseModel):
    """Request body for creating an event.

    event_id, seq, and ts are optional - server will generate if missing.
    """

    event_id: str | None = None
    session_id: str
    seq: int | None = None
    ts: datetime | None = None
    type: EventType

    parent_event_id: str | None = None
    head_id: str = "main"
    trail_version_id: str | None = None
    waypoint_id: str | None = None

    actor: Actor | None = None
    payload: dict[str, Any]

    @field_validator("session_id")
    @classmethod
    def validate_session_id_format(cls, v: str) -> str:
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError(
                "session_id must be 1-128 alphanumeric characters, underscores, or hyphens"
            )
        return v


class EventResponse(BaseModel):
    """Response after creating an event."""

    event_id: str
    seq: int
    ts: datetime


class SessionListItem(BaseModel):
    """Summary of a session for listing."""

    session_id: str
    event_count: int
    last_event_seq: int
    last_event_ts: datetime | None


# -----------------------------------------------------------------------------
# App factory
# -----------------------------------------------------------------------------


def create_app(
    db_path: str | Path = "pathway.db",
    require_api_key: bool | None = None,
    max_payload_size: int | None = None,
) -> FastAPI:
    """Create a FastAPI app with the given database.

    Args:
        db_path: Path to SQLite database, or ":memory:" for in-memory.
        require_api_key: If True, require X-API-Key header. If None, uses
                         PATHWAY_API_KEY env var (enabled if set).
        max_payload_size: Maximum request payload size in bytes. Defaults to
                         PATHWAY_MAX_PAYLOAD_SIZE env var or 1MB.

    Returns:
        Configured FastAPI application.
    """
    # Store instance (created before lifespan for access in endpoints)
    store = EventStore(db_path)

    # Determine API key requirement
    api_key = os.environ.get("PATHWAY_API_KEY")
    if require_api_key is None:
        require_api_key = api_key is not None

    # Determine payload size limit
    if max_payload_size is None:
        max_payload_size = MAX_PAYLOAD_SIZE

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        yield
        # Shutdown
        store.close()

    app = FastAPI(
        title="Pathway API",
        description="Learning-aware journey state model",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Store reference in app state
    app.state.store = store
    app.state.require_api_key = require_api_key
    app.state.api_key = api_key

    # -------------------------------------------------------------------------
    # Middleware for payload size limit
    # -------------------------------------------------------------------------

    @app.middleware("http")
    async def limit_payload_size(request: Request, call_next):
        """Reject requests with payload larger than max_payload_size."""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > max_payload_size:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Payload too large. Maximum size is {max_payload_size} bytes."},
            )
        return await call_next(request)

    # -------------------------------------------------------------------------
    # Dependency for API key verification
    # -------------------------------------------------------------------------

    async def verify_api_key(api_key_header: str | None = Depends(API_KEY_HEADER)):
        """Verify API key if required."""
        if not app.state.require_api_key:
            return
        if not api_key_header or api_key_header != app.state.api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key. Set X-API-Key header.",
            )

    # ---------------------------------------------------------------------
    # Endpoints
    # ---------------------------------------------------------------------

    @app.post("/events", response_model=EventResponse, dependencies=[Depends(verify_api_key)])
    async def create_event(request: EventRequest) -> EventResponse:
        """Append an event to the store.

        Auto-generates event_id (ULID) and seq if not provided.
        Auto-sets ts to now if not provided.
        Seq assignment is atomic to prevent race conditions.
        """
        # Generate missing fields
        event_id = request.event_id or str(ulid.new())
        ts = request.ts or datetime.now(timezone.utc)
        actor = request.actor or Actor(kind=ActorKind.SYSTEM)
        auto_seq = request.seq is None

        # Use 0 as placeholder if auto_seq - will be replaced atomically
        seq = request.seq if request.seq is not None else 0

        event = EventEnvelope(
            event_id=event_id,
            session_id=request.session_id,
            seq=seq,
            ts=ts,
            type=request.type,
            parent_event_id=request.parent_event_id,
            head_id=request.head_id,
            trail_version_id=request.trail_version_id,
            waypoint_id=request.waypoint_id,
            actor=actor,
            payload=request.payload,
        )

        try:
            result = store.append(event, auto_seq=auto_seq)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        return EventResponse(
            event_id=result.event_id,
            seq=result.seq,
            ts=result.ts,
        )

    @app.get("/session/{session_id}/state", response_model=SessionState)
    async def get_session_state(session_id: str) -> SessionState:
        """Get the derived state for a session.

        Returns JourneyView, LearnedView, and ArtifactView.
        """
        validate_session_id(session_id)
        if not store.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        events = store.get_events(session_id)
        return reduce_session_state(session_id, events)

    @app.get("/session/{session_id}/events", response_model=list[EventEnvelope])
    async def get_session_events(
        session_id: str,
        head_id: str | None = Query(None, description="Filter by branch"),
        from_seq: int | None = Query(None, description="Start from this seq"),
        to_seq: int | None = Query(None, description="End at this seq"),
        event_type: EventType | None = Query(None, description="Filter by event type"),
    ) -> list[EventEnvelope]:
        """Get raw events for a session with optional filters."""
        validate_session_id(session_id)
        if not store.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        return store.get_events(
            session_id,
            head_id=head_id,
            from_seq=from_seq,
            to_seq=to_seq,
            event_type=event_type,
        )

    @app.get("/sessions", response_model=list[SessionListItem])
    async def list_sessions() -> list[SessionListItem]:
        """List all sessions in the store."""
        sessions = []
        for session_id in store.list_sessions():
            events = store.get_events(session_id)
            last_event = events[-1] if events else None
            sessions.append(
                SessionListItem(
                    session_id=session_id,
                    event_count=len(events),
                    last_event_seq=last_event.seq if last_event else -1,
                    last_event_ts=last_event.ts if last_event else None,
                )
            )
        return sessions

    @app.get("/event/{event_id}", response_model=EventEnvelope)
    async def get_event(event_id: str) -> EventEnvelope:
        """Get a single event by ID."""
        event = store.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event

    return app


# Default app instance
app = create_app()
