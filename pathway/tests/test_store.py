"""Tests for the SQLite event store."""

import pytest
from datetime import datetime, timezone

from pathway.models.events import EventEnvelope, EventType, Actor, ActorKind
from pathway.store.sqlite_store import EventStore


@pytest.fixture
def store():
    """Create an in-memory store for testing."""
    return EventStore(":memory:")


def make_event(
    event_id: str,
    session_id: str = "test_sess",
    seq: int = 0,
    event_type: EventType = EventType.INTENT_CREATED,
    head_id: str = "main",
    parent_event_id: str | None = None,
) -> EventEnvelope:
    """Helper to create test events."""
    return EventEnvelope(
        event_id=event_id,
        session_id=session_id,
        seq=seq,
        ts=datetime.now(timezone.utc),
        type=event_type,
        head_id=head_id,
        parent_event_id=parent_event_id,
        actor=Actor(kind=ActorKind.SYSTEM),
        payload={"test": True},
    )


def test_append_and_get(store: EventStore):
    """Test basic append and retrieval."""
    event = make_event("e001")
    result = store.append(event)

    assert result.event_id == "e001"

    retrieved = store.get_event("e001")
    assert retrieved is not None
    assert retrieved.event_id == "e001"


def test_auto_seq(store: EventStore):
    """Test auto-assignment of seq numbers using get_next_seq."""
    # Use get_next_seq to simulate auto-assignment
    seq1 = store.get_next_seq("test_sess")
    e1 = make_event("e001", seq=seq1)
    result1 = store.append(e1)
    assert result1.seq == 0

    seq2 = store.get_next_seq("test_sess")
    e2 = make_event("e002", seq=seq2)
    result2 = store.append(e2)
    assert result2.seq == 1


def test_get_events_ordered(store: EventStore):
    """Test that events are returned in seq order."""
    store.append(make_event("e003", seq=2))
    store.append(make_event("e001", seq=0))
    store.append(make_event("e002", seq=1))

    events = store.get_events("test_sess")
    assert [e.event_id for e in events] == ["e001", "e002", "e003"]


def test_get_events_filter_by_head(store: EventStore):
    """Test filtering events by head_id."""
    store.append(make_event("e001", seq=0, head_id="main"))
    store.append(make_event("e002", seq=1, head_id="b1"))
    store.append(make_event("e003", seq=2, head_id="main"))

    main_events = store.get_events("test_sess", head_id="main")
    assert len(main_events) == 2

    b1_events = store.get_events("test_sess", head_id="b1")
    assert len(b1_events) == 1


def test_get_events_filter_by_seq_range(store: EventStore):
    """Test filtering events by seq range."""
    for i in range(5):
        store.append(make_event(f"e{i:03d}", seq=i))

    events = store.get_events("test_sess", from_seq=1, to_seq=3)
    assert len(events) == 3
    assert [e.seq for e in events] == [1, 2, 3]


def test_get_children(store: EventStore):
    """Test getting child events."""
    store.append(make_event("e001", seq=0))
    store.append(make_event("e002", seq=1, parent_event_id="e001"))
    store.append(make_event("e003", seq=2, parent_event_id="e001"))
    store.append(make_event("e004", seq=3, parent_event_id="e002"))

    children = store.get_children("e001")
    assert len(children) == 2
    assert {e.event_id for e in children} == {"e002", "e003"}


def test_get_all_heads(store: EventStore):
    """Test getting all unique head_ids."""
    store.append(make_event("e001", seq=0, head_id="main"))
    store.append(make_event("e002", seq=1, head_id="b1"))
    store.append(make_event("e003", seq=2, head_id="b2"))

    heads = store.get_all_heads("test_sess")
    assert set(heads) == {"main", "b1", "b2"}


def test_get_head_tip(store: EventStore):
    """Test getting the latest event on a head."""
    store.append(make_event("e001", seq=0, head_id="main"))
    store.append(make_event("e002", seq=1, head_id="main"))
    store.append(make_event("e003", seq=2, head_id="b1"))

    tip = store.get_head_tip("test_sess", "main")
    assert tip is not None
    assert tip.event_id == "e002"


def test_get_active_head(store: EventStore):
    """Test getting the active head."""
    store.append(make_event("e001", seq=0, head_id="main"))
    store.append(make_event("e002", seq=1, head_id="b1"))
    store.append(make_event("e003", seq=2, head_id="main"))

    active = store.get_active_head("test_sess")
    assert active == "main"


def test_session_exists(store: EventStore):
    """Test session existence check."""
    assert not store.session_exists("test_sess")

    store.append(make_event("e001"))
    assert store.session_exists("test_sess")


def test_list_sessions(store: EventStore):
    """Test listing all sessions."""
    store.append(make_event("e001", session_id="sess1", seq=0))
    store.append(make_event("e002", session_id="sess2", seq=0))
    store.append(make_event("e003", session_id="sess1", seq=1))

    sessions = store.list_sessions()
    assert set(sessions) == {"sess1", "sess2"}


def test_duplicate_event_id_fails(store: EventStore):
    """Test that duplicate event_ids are rejected."""
    store.append(make_event("e001", seq=0))

    with pytest.raises(ValueError):
        store.append(make_event("e001", seq=1))


def test_duplicate_seq_fails(store: EventStore):
    """Test that duplicate seq numbers are rejected."""
    store.append(make_event("e001", seq=0))

    with pytest.raises(ValueError):
        store.append(make_event("e002", seq=0))
