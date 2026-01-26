"""Session reducer - combines all reducers into a single state.

This is the main entry point for computing derived state from events.

State Semantics (GET /session/{id}/state):
------------------------------------------
- JourneyView: Tracks the active head. Shows current waypoint, branches,
  visited waypoints on the active path. Filtered by head for navigation.

- LearnedView: GLOBAL across all events in the session DAG.
  Learning persists across backtracking and branches.
  If you learn something on a failed path, you keep that knowledge.

- ArtifactView: Shows all artifacts. Active/superseded status is global
  (based on ArtifactSuperseded events), not filtered by head.
  Future: may add ?scope=head filter.

Design rationale:
- Journey = where you ARE (head-specific)
- Learned = what you KNOW (global, persistent)
- Artifacts = what you MADE (global, with version history)
"""

from pathway.models.events import EventEnvelope
from pathway.models.derived import SessionState, JourneyView, LearnedView, ArtifactView
from pathway.reducers.journey import reduce_journey
from pathway.reducers.learned import reduce_learned
from pathway.reducers.artifacts import reduce_artifacts


def reduce_session_state(
    session_id: str,
    events: list[EventEnvelope],
) -> SessionState:
    """Reduce all events to a complete SessionState.

    This is the main reducer that computes all derived views.

    Args:
        session_id: The session ID.
        events: All events for the session, ordered by seq.

    Returns:
        The complete SessionState.
    """
    journey = reduce_journey(events)
    learned = reduce_learned(events)
    artifacts = reduce_artifacts(events)

    last_event = events[-1] if events else None

    return SessionState(
        session_id=session_id,
        journey=journey,
        learned=learned,
        artifacts=artifacts,
        event_count=len(events),
        last_event_seq=last_event.seq if last_event else -1,
        last_event_ts=last_event.ts if last_event else None,
    )
