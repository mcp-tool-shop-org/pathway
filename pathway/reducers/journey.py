"""Journey reducer - computes the current navigation state.

The JourneyView tells you:
- Where the user is (current waypoint)
- What branch they're on (active head)
- What branches exist (branch tips)
- Where they've been (visited waypoints)
- Where they can go back to (backtrack targets)
"""

from pathway.models.events import (
    EventEnvelope,
    EventType,
    WaypointEnteredPayload,
    BacktrackedPayload,
    TrailVersionCreatedPayload,
)
from pathway.models.derived import JourneyView, VisitedWaypoint, BranchTip


def reduce_journey(events: list[EventEnvelope]) -> JourneyView:
    """Reduce events to a JourneyView.

    Args:
        events: All events for a session, ordered by seq.

    Returns:
        The computed JourneyView.
    """
    if not events:
        return JourneyView()

    view = JourneyView()

    # Track state as we process events
    branch_tips: dict[str, BranchTip] = {}
    visited: list[VisitedWaypoint] = []
    current_waypoint_id: str | None = None
    active_trail_version_id: str | None = None

    # Events we can backtrack to (waypoint entries that aren't superseded)
    backtrack_candidates: list[str] = []

    for event in events:
        # Update branch tip for this head
        branch_tips[event.head_id] = BranchTip(
            head_id=event.head_id,
            event_id=event.event_id,
            waypoint_id=event.waypoint_id,
            seq=event.seq,
        )

        # Process by event type
        if event.type == EventType.TRAIL_VERSION_CREATED:
            payload = TrailVersionCreatedPayload.model_validate(event.payload)
            active_trail_version_id = payload.trail_version_id

        elif event.type == EventType.WAYPOINT_ENTERED:
            payload = WaypointEnteredPayload.model_validate(event.payload)
            current_waypoint_id = payload.waypoint_id

            # Record visit
            visited.append(
                VisitedWaypoint(
                    waypoint_id=payload.waypoint_id,
                    timestamp=event.ts,
                    event_id=event.event_id,
                )
            )

            # Add to backtrack candidates (unless it's a backtrack itself)
            if payload.via != "backtrack":
                backtrack_candidates.append(event.event_id)

        elif event.type == EventType.BACKTRACKED:
            payload = BacktrackedPayload.model_validate(event.payload)
            # After backtrack, the to_event_id becomes relevant for context
            # but current_waypoint_id should be updated by next WaypointEntered

        elif event.type == EventType.STEP_COMPLETED:
            # Step completion doesn't change waypoint, just records progress
            pass

        elif event.type == EventType.CHOICE_MADE:
            # Choice made leads to waypoint change via WaypointEntered
            pass

        elif event.type == EventType.BLOCKED:
            # Blocked state - user is stuck at current waypoint
            pass

        elif event.type == EventType.REPLANNED:
            # Replanned - new trail version will be created
            pass

        elif event.type == EventType.MERGED:
            # Merged - multiple branches converge
            pass

    # Get the latest event to determine active head
    latest_event = events[-1]

    view.head_event_id = latest_event.event_id
    view.current_waypoint_id = current_waypoint_id
    view.active_head_id = latest_event.head_id
    view.active_trail_version_id = active_trail_version_id
    view.branch_tips = branch_tips
    view.visited_waypoints = visited
    view.backtrack_targets = backtrack_candidates

    return view


def get_branch_divergence_point(
    events: list[EventEnvelope],
    head_id: str,
) -> str | None:
    """Find where a branch diverged from main.

    Args:
        events: All events for a session.
        head_id: The branch to analyze.

    Returns:
        The event_id where the branch diverged, or None if it's main.
    """
    if head_id == "main":
        return None

    # Find the first event on this branch
    branch_events = [e for e in events if e.head_id == head_id]
    if not branch_events:
        return None

    first_branch_event = min(branch_events, key=lambda e: e.seq)
    return first_branch_event.parent_event_id


def get_path_to_waypoint(
    events: list[EventEnvelope],
    target_waypoint_id: str,
) -> list[str]:
    """Get the sequence of waypoints leading to a target.

    Args:
        events: All events for a session.
        target_waypoint_id: The waypoint to trace back from.

    Returns:
        List of waypoint_ids from start to target.
    """
    # Find all WaypointEntered events
    waypoint_events = [
        e for e in events if e.type == EventType.WAYPOINT_ENTERED
    ]

    # Build path by tracing WaypointEntered events
    path: list[str] = []
    for event in waypoint_events:
        payload = WaypointEnteredPayload.model_validate(event.payload)
        path.append(payload.waypoint_id)
        if payload.waypoint_id == target_waypoint_id:
            break

    return path
