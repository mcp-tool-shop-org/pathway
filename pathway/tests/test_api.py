"""Tests for the FastAPI endpoints."""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from pathway.api.main import create_app
from pathway.models.events import EventType


@pytest.fixture
def client():
    """Create a test client with in-memory database."""
    app = create_app(":memory:")
    return TestClient(app)


def test_create_event(client: TestClient):
    """Test creating an event via POST /events."""
    response = client.post("/events", json={
        "session_id": "test_sess",
        "type": "IntentCreated",
        "payload": {"goal": "Test goal"},
    })
    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data
    assert data["seq"] == 0


def test_create_event_auto_seq(client: TestClient):
    """Test that seq is auto-incremented."""
    # First event
    r1 = client.post("/events", json={
        "session_id": "test_sess",
        "type": "IntentCreated",
        "payload": {"goal": "Test"},
    })
    assert r1.json()["seq"] == 0

    # Second event
    r2 = client.post("/events", json={
        "session_id": "test_sess",
        "type": "WaypointEntered",
        "payload": {"waypoint_id": "w0"},
    })
    assert r2.json()["seq"] == 1


def test_get_session_state(client: TestClient):
    """Test GET /session/{id}/state."""
    # Create some events
    client.post("/events", json={
        "session_id": "test_sess",
        "type": "IntentCreated",
        "payload": {"goal": "Test"},
    })
    client.post("/events", json={
        "session_id": "test_sess",
        "type": "WaypointEntered",
        "waypoint_id": "w0",
        "payload": {"waypoint_id": "w0", "via": "next"},
    })
    client.post("/events", json={
        "session_id": "test_sess",
        "type": "ConceptLearned",
        "payload": {"concept_id": "concept.test", "confidence_delta": 0.5},
    })

    response = client.get("/session/test_sess/state")
    assert response.status_code == 200

    state = response.json()
    assert state["session_id"] == "test_sess"
    assert state["event_count"] == 3
    assert "journey" in state
    assert "learned" in state
    assert "artifacts" in state


def test_get_session_state_not_found(client: TestClient):
    """Test GET /session/{id}/state with non-existent session."""
    response = client.get("/session/nonexistent/state")
    assert response.status_code == 404


def test_get_session_events(client: TestClient):
    """Test GET /session/{id}/events."""
    # Create events
    for i in range(3):
        client.post("/events", json={
            "session_id": "test_sess",
            "type": "WaypointEntered",
            "payload": {"waypoint_id": f"w{i}"},
        })

    response = client.get("/session/test_sess/events")
    assert response.status_code == 200

    events = response.json()
    assert len(events) == 3


def test_get_session_events_with_filters(client: TestClient):
    """Test GET /session/{id}/events with query filters."""
    # Create events on different heads
    client.post("/events", json={
        "session_id": "test_sess",
        "type": "WaypointEntered",
        "head_id": "main",
        "payload": {"waypoint_id": "w0"},
    })
    client.post("/events", json={
        "session_id": "test_sess",
        "type": "WaypointEntered",
        "head_id": "b1",
        "payload": {"waypoint_id": "w1"},
    })

    # Filter by head
    response = client.get("/session/test_sess/events?head_id=main")
    assert len(response.json()) == 1


def test_list_sessions(client: TestClient):
    """Test GET /sessions."""
    # Create events in different sessions
    client.post("/events", json={
        "session_id": "sess1",
        "type": "IntentCreated",
        "payload": {"goal": "Test 1"},
    })
    client.post("/events", json={
        "session_id": "sess2",
        "type": "IntentCreated",
        "payload": {"goal": "Test 2"},
    })

    response = client.get("/sessions")
    assert response.status_code == 200

    sessions = response.json()
    assert len(sessions) == 2
    session_ids = {s["session_id"] for s in sessions}
    assert session_ids == {"sess1", "sess2"}


def test_get_event(client: TestClient):
    """Test GET /event/{event_id}."""
    # Create an event with known ID
    client.post("/events", json={
        "event_id": "known_id",
        "session_id": "test_sess",
        "type": "IntentCreated",
        "payload": {"goal": "Test"},
    })

    response = client.get("/event/known_id")
    assert response.status_code == 200
    assert response.json()["event_id"] == "known_id"


def test_get_event_not_found(client: TestClient):
    """Test GET /event/{event_id} with non-existent event."""
    response = client.get("/event/nonexistent")
    assert response.status_code == 404


def test_duplicate_event_id_rejected(client: TestClient):
    """Test that duplicate event_ids are rejected."""
    client.post("/events", json={
        "event_id": "dup_id",
        "session_id": "test_sess",
        "type": "IntentCreated",
        "payload": {"goal": "Test"},
    })

    response = client.post("/events", json={
        "event_id": "dup_id",
        "session_id": "test_sess",
        "type": "WaypointEntered",
        "payload": {"waypoint_id": "w0"},
    })
    assert response.status_code == 409
