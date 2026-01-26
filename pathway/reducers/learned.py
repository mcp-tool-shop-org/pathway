"""Learned reducer - aggregates knowledge about the user.

The LearnedView tracks:
- Preferences: How the user likes to learn
- Constraints: Hard facts about their environment
- Concepts: What mental models they've built

Key invariant: Learning persists across backtracking.
When the user backtracks, they keep what they learned on the abandoned path.
"""

from pathway.models.events import (
    EventEnvelope,
    EventType,
    EvidenceRef,
    PreferenceLearnedPayload,
    ConceptLearnedPayload,
    ConstraintLearnedPayload,
)
from pathway.models.derived import LearnedView, LearnedRecord


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value to a range."""
    return max(min_val, min(max_val, value))


def reduce_learned(events: list[EventEnvelope]) -> LearnedView:
    """Reduce events to a LearnedView.

    Processes PreferenceLearned, ConceptLearned, and ConstraintLearned events
    to build aggregate confidence scores with evidence.

    Args:
        events: All events for a session, ordered by seq.

    Returns:
        The computed LearnedView.
    """
    view = LearnedView()

    for event in events:
        if event.type == EventType.PREFERENCE_LEARNED:
            payload = PreferenceLearnedPayload.model_validate(event.payload)
            _update_learned_record(
                records=view.preferences,
                id_=payload.preference_id,
                value=payload.value,
                confidence_delta=payload.confidence_delta,
                evidence=payload.evidence,
                seq=event.seq,
            )

        elif event.type == EventType.CONCEPT_LEARNED:
            payload = ConceptLearnedPayload.model_validate(event.payload)
            _update_learned_record(
                records=view.concepts,
                id_=payload.concept_id,
                value=None,  # Concepts don't have values, just confidence
                confidence_delta=payload.confidence_delta,
                evidence=payload.evidence,
                seq=event.seq,
            )

        elif event.type == EventType.CONSTRAINT_LEARNED:
            payload = ConstraintLearnedPayload.model_validate(event.payload)
            _update_learned_record(
                records=view.constraints,
                id_=payload.constraint_id,
                value=payload.value,
                confidence_delta=payload.confidence_delta,
                evidence=payload.evidence,
                seq=event.seq,
            )

    return view


def _update_learned_record(
    records: dict[str, LearnedRecord],
    id_: str,
    value: any,
    confidence_delta: float,
    evidence: list[EvidenceRef] | None,
    seq: int,
) -> None:
    """Update or create a learned record.

    Args:
        records: The dict of records to update.
        id_: The preference/concept/constraint ID.
        value: The value (for preferences/constraints, None for concepts).
        confidence_delta: Change in confidence.
        evidence: Supporting evidence refs.
        seq: Event sequence number.
    """
    if id_ in records:
        record = records[id_]
        # Update existing record
        new_confidence = clamp(record.confidence + confidence_delta)
        new_evidence = list(record.evidence)
        if evidence:
            new_evidence.extend(evidence)

        records[id_] = LearnedRecord(
            id=id_,
            value=value if value is not None else record.value,
            confidence=new_confidence,
            evidence=new_evidence,
            updated_at_seq=seq,
        )
    else:
        # Create new record
        records[id_] = LearnedRecord(
            id=id_,
            value=value,
            confidence=clamp(confidence_delta),  # Start from 0 + delta
            evidence=list(evidence) if evidence else [],
            updated_at_seq=seq,
        )


def get_high_confidence_concepts(
    view: LearnedView,
    threshold: float = 0.5,
) -> list[str]:
    """Get concepts the user understands well.

    Args:
        view: The LearnedView to query.
        threshold: Minimum confidence to include.

    Returns:
        List of concept IDs above the threshold.
    """
    return [
        concept_id
        for concept_id, record in view.concepts.items()
        if record.confidence >= threshold
    ]


def get_active_constraints(view: LearnedView) -> dict[str, any]:
    """Get constraints with their values.

    Args:
        view: The LearnedView to query.

    Returns:
        Dict mapping constraint_id to value.
    """
    return {
        constraint_id: record.value
        for constraint_id, record in view.constraints.items()
        if record.value is not None
    }


def get_user_preferences(view: LearnedView) -> dict[str, any]:
    """Get preferences with their values.

    Args:
        view: The LearnedView to query.

    Returns:
        Dict mapping preference_id to value.
    """
    return {
        pref_id: record.value
        for pref_id, record in view.preferences.items()
        if record.value is not None
    }


def summarize_learned(view: LearnedView) -> dict:
    """Create a human-readable summary of learned state.

    Args:
        view: The LearnedView to summarize.

    Returns:
        Dict with summary statistics.
    """
    return {
        "total_preferences": len(view.preferences),
        "total_constraints": len(view.constraints),
        "total_concepts": len(view.concepts),
        "high_confidence_concepts": len(get_high_confidence_concepts(view)),
        "preferences": get_user_preferences(view),
        "constraints": get_active_constraints(view),
    }
