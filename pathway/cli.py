"""CLI tools for Pathway.

Commands:
- init: Initialize a new database
- import: Import events from JSONL
- export: Export events to JSONL
- state: Print derived state for a session
- events: List events for a session
- sessions: List all sessions
- serve: Start the API server
- doctor: Run health checks on the database
"""

import argparse
import json
import sys
from multiprocessing import freeze_support
from pathlib import Path

from pathway.store.sqlite_store import EventStore
from pathway.store.jsonl_io import import_session_jsonl, export_session_jsonl
from pathway.reducers.session import reduce_session_state


DEFAULT_DB = "pathway.db"


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new database."""
    db_path = Path(args.db)

    if db_path.exists() and not args.force:
        print(f"Database already exists: {db_path}")
        print("Use --force to overwrite.")
        return 1

    if db_path.exists():
        db_path.unlink()

    store = EventStore(db_path)
    store.close()
    print(f"Initialized database: {db_path}")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    """Import events from JSONL."""
    db_path = Path(args.db)
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    store = EventStore(db_path)
    try:
        count = import_session_jsonl(
            store,
            input_path,
            session_id_override=args.session_id,
        )
        print(f"Imported {count} events from {input_path}")
        return 0
    except ValueError as e:
        print(f"Import error: {e}")
        return 1
    finally:
        store.close()


def cmd_export(args: argparse.Namespace) -> int:
    """Export events to JSONL."""
    db_path = Path(args.db)
    output_path = Path(args.output)

    store = EventStore(db_path)
    try:
        if not store.session_exists(args.session_id):
            print(f"Session not found: {args.session_id}")
            return 1

        count = export_session_jsonl(store, args.session_id, output_path)
        print(f"Exported {count} events to {output_path}")
        return 0
    finally:
        store.close()


def cmd_state(args: argparse.Namespace) -> int:
    """Print derived state for a session."""
    db_path = Path(args.db)

    store = EventStore(db_path)
    try:
        if not store.session_exists(args.session_id):
            print(f"Session not found: {args.session_id}")
            return 1

        events = store.get_events(args.session_id)
        state = reduce_session_state(args.session_id, events)

        if args.json:
            print(state.model_dump_json(indent=2))
        else:
            _print_state_summary(state)

        return 0
    finally:
        store.close()


def _print_state_summary(state) -> None:
    """Print a human-readable state summary."""
    print(f"Session: {state.session_id}")
    print(f"Events: {state.event_count}")
    print(f"Last seq: {state.last_event_seq}")
    print()

    # Journey
    j = state.journey
    print("=== Journey ===")
    print(f"  Active head: {j.active_head_id}")
    print(f"  Current waypoint: {j.current_waypoint_id or '(none)'}")
    print(f"  Trail version: {j.active_trail_version_id or '(none)'}")
    print(f"  Branches: {list(j.branch_tips.keys())}")
    print(f"  Visited waypoints: {len(j.visited_waypoints)}")
    print(f"  Backtrack targets: {len(j.backtrack_targets)}")
    print()

    # Learned
    l = state.learned
    print("=== Learned ===")
    print(f"  Preferences: {len(l.preferences)}")
    for pref_id, record in l.preferences.items():
        print(f"    {pref_id}: {record.value} (conf={record.confidence:.2f})")
    print(f"  Constraints: {len(l.constraints)}")
    for con_id, record in l.constraints.items():
        print(f"    {con_id}: {record.value} (conf={record.confidence:.2f})")
    print(f"  Concepts: {len(l.concepts)}")
    for con_id, record in l.concepts.items():
        print(f"    {con_id}: conf={record.confidence:.2f}")
    print()

    # Artifacts
    a = state.artifacts
    print("=== Artifacts ===")
    print(f"  Total: {len(a.artifacts)}")
    print(f"  Active: {len(a.active_artifacts)}")
    print(f"  Superseded: {len(a.superseded_artifacts)}")
    for artifact_id, record in a.artifacts.items():
        status = "active" if record.is_active else f"superseded by {record.superseded_by}"
        print(f"    {artifact_id} ({record.type.value}): {status}")


def cmd_events(args: argparse.Namespace) -> int:
    """List events for a session."""
    db_path = Path(args.db)

    store = EventStore(db_path)
    try:
        if not store.session_exists(args.session_id):
            print(f"Session not found: {args.session_id}")
            return 1

        events = store.get_events(
            args.session_id,
            head_id=args.head,
            from_seq=args.from_seq,
            to_seq=args.to_seq,
        )

        if args.json:
            print("[")
            for i, event in enumerate(events):
                comma = "," if i < len(events) - 1 else ""
                print(f"  {event.model_dump_json()}{comma}")
            print("]")
        else:
            for event in events:
                print(f"[{event.seq:04d}] {event.type.value} ({event.head_id})")
                print(f"       id: {event.event_id}")
                print(f"       ts: {event.ts}")
                if event.waypoint_id:
                    print(f"       waypoint: {event.waypoint_id}")
                print()

        return 0
    finally:
        store.close()


def cmd_sessions(args: argparse.Namespace) -> int:
    """List all sessions."""
    db_path = Path(args.db)

    store = EventStore(db_path)
    try:
        sessions = store.list_sessions()

        if not sessions:
            print("No sessions found.")
            return 0

        for session_id in sessions:
            events = store.get_events(session_id)
            last_event = events[-1] if events else None
            print(f"{session_id}")
            print(f"  Events: {len(events)}")
            if last_event:
                print(f"  Last: {last_event.ts}")
            print()

        return 0
    finally:
        store.close()


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the API server."""
    try:
        import uvicorn
        from pathway.api.main import create_app
    except ImportError:
        print("uvicorn not installed. Run: pip install uvicorn")
        return 1

    app = create_app(args.db)
    print(f"Starting Pathway API server on http://{args.host}:{args.port}")
    print(f"Database: {args.db}")

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run health checks on the database.

    Checks:
    1. Schema validation
    2. Event validation (all events parse correctly)
    3. Seq monotonicity (no gaps or duplicates per session)
    4. Parent references (all parent_event_ids exist)
    5. Reducer replay (no crashes)
    """
    db_path = Path(args.db)

    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        return 1

    print(f"Checking database: {db_path}")
    print("=" * 50)

    issues = []
    warnings = []

    store = EventStore(db_path)
    try:
        sessions = store.list_sessions()
        print(f"Sessions found: {len(sessions)}")

        total_events = 0
        for session_id in sessions:
            events = store.get_events(session_id)
            total_events += len(events)

            # Check 1: Seq monotonicity
            seqs = [e.seq for e in events]
            if seqs != sorted(seqs):
                issues.append(f"[{session_id}] Seqs not in order")
            if len(seqs) != len(set(seqs)):
                issues.append(f"[{session_id}] Duplicate seqs detected")

            expected_seqs = list(range(len(events)))
            if seqs != expected_seqs:
                warnings.append(f"[{session_id}] Seq gaps: expected {expected_seqs}, got {seqs}")

            # Check 2: Parent references
            event_ids = {e.event_id for e in events}
            for event in events:
                if event.parent_event_id and event.parent_event_id not in event_ids:
                    issues.append(
                        f"[{session_id}] Dangling parent_event_id: "
                        f"{event.event_id} -> {event.parent_event_id}"
                    )

            # Check 3: Event validation (payload parsing)
            for event in events:
                try:
                    event.get_payload_model()
                except Exception as e:
                    issues.append(f"[{session_id}] Invalid payload in {event.event_id}: {e}")

            # Check 4: Reducer replay
            try:
                state = reduce_session_state(session_id, events)
                print(f"  {session_id}: {len(events)} events, head={state.journey.active_head_id}")
            except Exception as e:
                issues.append(f"[{session_id}] Reducer crash: {e}")

        print(f"Total events: {total_events}")
        print("=" * 50)

        # Report results
        if warnings:
            print(f"\nWarnings ({len(warnings)}):")
            for w in warnings:
                print(f"  [WARN] {w}")

        if issues:
            print(f"\nIssues ({len(issues)}):")
            for issue in issues:
                print(f"  [FAIL] {issue}")
            print("\nDiagnosis: UNHEALTHY")
            return 1
        else:
            print("\n[OK] All checks passed")
            print("Diagnosis: HEALTHY")
            return 0

    finally:
        store.close()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pathway CLI - Learning-aware journey state model",
        prog="pathway",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help=f"Database path (default: {DEFAULT_DB})",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing")

    # import
    import_parser = subparsers.add_parser("import", help="Import from JSONL")
    import_parser.add_argument("input", help="Input JSONL file")
    import_parser.add_argument("--session-id", help="Override session ID")

    # export
    export_parser = subparsers.add_parser("export", help="Export to JSONL")
    export_parser.add_argument("session_id", help="Session to export")
    export_parser.add_argument("--output", "-o", required=True, help="Output file")

    # state
    state_parser = subparsers.add_parser("state", help="Print derived state")
    state_parser.add_argument("session_id", help="Session to show")
    state_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # events
    events_parser = subparsers.add_parser("events", help="List events")
    events_parser.add_argument("session_id", help="Session to show")
    events_parser.add_argument("--head", help="Filter by head")
    events_parser.add_argument("--from-seq", type=int, help="Start seq")
    events_parser.add_argument("--to-seq", type=int, help="End seq")
    events_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # sessions
    subparsers.add_parser("sessions", help="List all sessions")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    # doctor
    subparsers.add_parser("doctor", help="Run health checks on database")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "init": cmd_init,
        "import": cmd_import,
        "export": cmd_export,
        "state": cmd_state,
        "events": cmd_events,
        "sessions": cmd_sessions,
        "serve": cmd_serve,
        "doctor": cmd_doctor,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    freeze_support()
    sys.exit(main())
