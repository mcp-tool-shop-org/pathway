"""Artifacts reducer - tracks outputs produced during the journey.

The ArtifactView tracks:
- All artifacts ever created (code, docs, logs, etc.)
- Which ones are active vs superseded
- The supersedence chain (what replaced what)

Key invariant: Artifacts are never deleted, only superseded.
An artifact is active unless an ArtifactSuperseded event points away from it.
"""

from pathway.models.events import (
    EventEnvelope,
    EventType,
    ArtifactCreatedPayload,
    ArtifactSupersededPayload,
)
from pathway.models.derived import ArtifactView, ArtifactRecord


def reduce_artifacts(events: list[EventEnvelope]) -> ArtifactView:
    """Reduce events to an ArtifactView.

    Processes ArtifactCreated and ArtifactSuperseded events to build
    a complete picture of all artifacts and their status.

    Args:
        events: All events for a session, ordered by seq.

    Returns:
        The computed ArtifactView.
    """
    view = ArtifactView()

    for event in events:
        if event.type == EventType.ARTIFACT_CREATED:
            payload = ArtifactCreatedPayload.model_validate(event.payload)
            artifact = payload.artifact

            view.artifacts[artifact.artifact_id] = ArtifactRecord(
                artifact_id=artifact.artifact_id,
                type=artifact.type,
                title=artifact.title,
                content_ref=artifact.content_ref,
                produced_at_waypoint_id=artifact.produced_at_waypoint_id,
                produced_by_event_id=event.event_id,
                produced_at_seq=event.seq,
                reversible=artifact.reversible,
                side_effects=artifact.side_effects,
                superseded_by=None,
                is_active=True,
            )

        elif event.type == EventType.ARTIFACT_SUPERSEDED:
            payload = ArtifactSupersededPayload.model_validate(event.payload)

            if payload.artifact_id in view.artifacts:
                record = view.artifacts[payload.artifact_id]
                # Mark as superseded
                view.artifacts[payload.artifact_id] = ArtifactRecord(
                    artifact_id=record.artifact_id,
                    type=record.type,
                    title=record.title,
                    content_ref=record.content_ref,
                    produced_at_waypoint_id=record.produced_at_waypoint_id,
                    produced_by_event_id=record.produced_by_event_id,
                    produced_at_seq=record.produced_at_seq,
                    reversible=record.reversible,
                    side_effects=record.side_effects,
                    superseded_by=payload.superseded_by_artifact_id,
                    is_active=False,
                )

    return view


def get_artifact_chain(
    view: ArtifactView,
    artifact_id: str,
) -> list[str]:
    """Get the chain of artifacts leading to the current version.

    Follows supersedence backwards to find all previous versions.

    Args:
        view: The ArtifactView to query.
        artifact_id: The artifact to trace.

    Returns:
        List of artifact_ids from oldest to newest.
    """
    # Build reverse mapping: superseded_by -> original
    reverse_map: dict[str, str] = {}
    for record in view.artifacts.values():
        if record.superseded_by:
            reverse_map[record.superseded_by] = record.artifact_id

    # Trace backwards
    chain: list[str] = [artifact_id]
    current = artifact_id

    while current in reverse_map:
        predecessor = reverse_map[current]
        chain.insert(0, predecessor)
        current = predecessor

    return chain


def get_artifacts_by_type(
    view: ArtifactView,
    artifact_type: str,
    active_only: bool = True,
) -> list[ArtifactRecord]:
    """Get artifacts of a specific type.

    Args:
        view: The ArtifactView to query.
        artifact_type: The type to filter by.
        active_only: If True, only return active artifacts.

    Returns:
        List of matching ArtifactRecords.
    """
    return [
        record
        for record in view.artifacts.values()
        if record.type.value == artifact_type
        and (not active_only or record.is_active)
    ]


def get_artifacts_by_waypoint(
    view: ArtifactView,
    waypoint_id: str,
    active_only: bool = True,
) -> list[ArtifactRecord]:
    """Get artifacts produced at a specific waypoint.

    Args:
        view: The ArtifactView to query.
        waypoint_id: The waypoint to filter by.
        active_only: If True, only return active artifacts.

    Returns:
        List of matching ArtifactRecords.
    """
    return [
        record
        for record in view.artifacts.values()
        if record.produced_at_waypoint_id == waypoint_id
        and (not active_only or record.is_active)
    ]


def summarize_artifacts(view: ArtifactView) -> dict:
    """Create a human-readable summary of artifact state.

    Args:
        view: The ArtifactView to summarize.

    Returns:
        Dict with summary statistics.
    """
    type_counts: dict[str, int] = {}
    for record in view.artifacts.values():
        type_name = record.type.value
        type_counts[type_name] = type_counts.get(type_name, 0) + 1

    return {
        "total_artifacts": len(view.artifacts),
        "active_artifacts": len(view.active_artifacts),
        "superseded_artifacts": len(view.superseded_artifacts),
        "by_type": type_counts,
    }
