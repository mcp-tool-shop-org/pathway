# Pathway Core Test Coverage Requirements

**Goal**: Achieve 100% test coverage across all modules

**Current Status**:
- Source modules: 16 files (cli.py, api/main.py, models/*, store/*, reducers/*)
- Test files: 6 files (test_api.py, test_api_security.py, test_events.py, test_invariants.py, test_reducers.py, test_store.py)
- **Estimated coverage**: ~70-75% (good foundation but missing edge cases and CLI scenarios)

---

## Module: `pathway/cli.py` (400 lines)

### Currently Tested
- ❌ No direct CLI tests exist

### Missing Tests (Priority: CRITICAL - User interface)

#### 1. Init Command
**Lines**: 28-44

```python
def test_cmd_init_creates_database():
    """Test init command creates new database."""
    # pathway init
    # Should create pathway.db with schema

def test_cmd_init_no_overwrite():
    """Test init refuses to overwrite existing database."""
    # Create db first, then init again
    # Should fail unless --force

def test_cmd_init_force_overwrites():
    """Test --force flag overwrites existing database."""
    # init, then init --force
    # Should succeed and create fresh db

def test_cmd_init_custom_path():
    """Test init with custom database path."""
    # pathway init --db custom.db
    # Should create at custom path
```

#### 2. Import Command
**Lines**: 46-69

```python
def test_cmd_import_jsonl():
    """Test importing events from JSONL file."""
    # pathway import sample_session.jsonl
    # Should import all events

def test_cmd_import_with_session_override():
    """Test --session-id overrides JSONL session IDs."""
    # pathway import --session-id new_id file.jsonl
    # All events should use new_id

def test_cmd_import_file_not_found():
    """Test import with missing file."""
    # pathway import nonexistent.jsonl
    # Should error gracefully

def test_cmd_import_invalid_jsonl():
    """Test import with malformed JSONL."""
    # Invalid JSON in file
    # Should error with clear message

def test_cmd_import_empty_file():
    """Test import with empty JSONL file."""
    # Empty file
    # Should succeed with 0 imports
```

#### 3. Export Command
**Lines**: 71-87

```python
def test_cmd_export_session():
    """Test exporting session to JSONL."""
    # pathway export sess_001 -o output.jsonl
    # Should export all events

def test_cmd_export_session_not_found():
    """Test export with non-existent session."""
    # pathway export nonexistent
    # Should error

def test_cmd_export_overwrites_existing():
    """Test export overwrites existing file."""
    # Create output.jsonl, then export
    # Should overwrite

def test_cmd_export_custom_output_path():
    """Test export to custom path."""
    # pathway export sess_001 -o /tmp/custom.jsonl
    # Should create file at path
```

#### 4. State Command
**Lines**: 89-153

```python
def test_cmd_state_displays_summary():
    """Test state command shows session summary."""
    # pathway state sess_001
    # Should display journey, learned, artifacts

def test_cmd_state_json_output():
    """Test --json flag outputs JSON."""
    # pathway state --json sess_001
    # Should output valid JSON

def test_cmd_state_session_not_found():
    """Test state with non-existent session."""
    # pathway state nonexistent
    # Should error

def test_state_print_journey_section():
    """Test journey state printing."""
    # Journey with branches, waypoints
    # Should format nicely

def test_state_print_learned_section():
    """Test learned state printing."""
    # Preferences, concepts, constraints
    # Should show confidence scores

def test_state_print_artifacts_section():
    """Test artifacts state printing."""
    # Active and superseded artifacts
    # Should show supersedence chains

def test_state_empty_session():
    """Test state with session with no events."""
    # Empty session
    # Should show empty state
```

#### 5. Events Command
**Lines**: 155-190

```python
def test_cmd_events_lists_all():
    """Test events command lists all events."""
    # pathway events sess_001
    # Should list all events with details

def test_cmd_events_filter_by_type():
    """Test --type filter."""
    # pathway events --type IntentCreated sess_001
    # Should only show that type

def test_cmd_events_limit():
    """Test --limit flag."""
    # pathway events --limit 10 sess_001
    # Should show only 10 events

def test_cmd_events_json_output():
    """Test --json flag for events."""
    # pathway events --json sess_001
    # Should output JSON array

def test_cmd_events_session_not_found():
    """Test events with non-existent session."""
    # pathway events nonexistent
    # Should error

def test_cmd_events_verbose():
    """Test --verbose shows full payloads."""
    # pathway events --verbose sess_001
    # Should show full event details
```

#### 6. Sessions Command
**Lines**: 192-216

```python
def test_cmd_sessions_lists_all():
    """Test sessions command lists all sessions."""
    # pathway sessions
    # Should list all with event counts

def test_cmd_sessions_empty_database():
    """Test sessions with no sessions."""
    # Empty db
    # Should show "No sessions found"

def test_cmd_sessions_shows_metadata():
    """Test sessions shows event count and timestamps."""
    # Multiple sessions
    # Should show count, last event time

def test_cmd_sessions_json_output():
    """Test --json flag for sessions."""
    # pathway sessions --json
    # Should output JSON array
```

#### 7. Serve Command
**Lines**: 218-233

```python
def test_cmd_serve_starts_server():
    """Test serve command starts API server."""
    # pathway serve
    # Should start uvicorn on default port

def test_cmd_serve_custom_host_port():
    """Test --host and --port flags."""
    # pathway serve --host 0.0.0.0 --port 9000
    # Should bind to specified address

def test_cmd_serve_missing_uvicorn():
    """Test serve fails gracefully without uvicorn."""
    # Mock ImportError for uvicorn
    # Should show helpful error
```

#### 8. Doctor Command
**Lines**: 235-323

```python
def test_cmd_doctor_healthy_database():
    """Test doctor on healthy database."""
    # Valid db with correct data
    # Should report no issues

def test_cmd_doctor_seq_gaps():
    """Test doctor detects seq gaps."""
    # Events with non-contiguous seqs
    # Should warn about gaps

def test_cmd_doctor_duplicate_seqs():
    """Test doctor detects duplicate seqs."""
    # Same seq used twice in session
    # Should report issue

def test_cmd_doctor_dangling_parent_refs():
    """Test doctor detects dangling parent_event_id."""
    # Event references non-existent parent
    # Should report issue

def test_cmd_doctor_invalid_payload():
    """Test doctor detects invalid event payloads."""
    # Event with malformed payload
    # Should report parsing error

def test_cmd_doctor_reducer_crash():
    """Test doctor detects reducer failures."""
    # Events that cause reducer to crash
    # Should report reducer error

def test_cmd_doctor_database_not_found():
    """Test doctor with missing database."""
    # pathway doctor --db nonexistent.db
    # Should error clearly
```

#### 9. Main Entry Point
**Lines**: 325-400

```python
def test_cli_help():
    """Test --help flag."""
    # pathway --help
    # Should show usage

def test_cli_version():
    """Test --version flag."""
    # pathway --version
    # Should show version

def test_cli_invalid_command():
    """Test invalid command."""
    # pathway invalid_cmd
    # Should show error and usage

def test_cli_missing_required_args():
    """Test command with missing args."""
    # pathway export (no session_id)
    # Should show error

def test_cli_database_arg_global():
    """Test --db flag works for all commands."""
    # pathway --db custom.db <command>
    # All commands should use custom db
```

---

## Module: `pathway/api/main.py` (297 lines)

### Currently Tested
- ✅ Basic API endpoints tested
- ✅ API key authentication tested
- ✅ Session ID validation tested
- ✅ Payload size limiting tested

### Missing Tests (Priority: MEDIUM - Already well covered)

#### 1. Event Creation Edge Cases
**Lines**: 192-232

```python
def test_create_event_with_explicit_seq():
    """Test creating event with explicit seq number."""
    # seq=5 provided in request
    # Should use that seq (if valid)

def test_create_event_with_explicit_event_id():
    """Test creating event with explicit event_id."""
    # event_id provided
    # Should use that ID

def test_create_event_with_timestamp():
    """Test creating event with explicit timestamp."""
    # ts provided
    # Should use that timestamp

def test_create_event_auto_seq_race():
    """Test concurrent event creation uses correct seq."""
    # Multiple simultaneous requests
    # Seqs should be unique and ordered

def test_create_event_invalid_type():
    """Test creating event with invalid type."""
    # type="InvalidType"
    # Should error 422

def test_create_event_missing_required_fields():
    """Test creating event without required fields."""
    # Missing payload
    # Should error 422
```

#### 2. Session State Edge Cases
**Lines**: 234-245

```python
def test_get_session_state_empty_session():
    """Test getting state for session with no events."""
    # Session exists but no events yet
    # Should return empty state views

def test_get_session_state_reducer_error():
    """Test handling reducer errors gracefully."""
    # Events that cause reducer to fail
    # Should return 500 with error details
```

#### 3. Event Filtering
**Lines**: 247-266

```python
def test_get_session_events_filter_type():
    """Test filtering events by type."""
    # ?type=IntentCreated
    # Should only return that type

def test_get_session_events_filter_seq_range():
    """Test filtering events by seq range."""
    # ?seq_min=5&seq_max=10
    # Should return events 5-10

def test_get_session_events_filter_head():
    """Test filtering events by head_id."""
    # ?head_id=main
    # Should only return main branch events

def test_get_session_events_multiple_filters():
    """Test combining multiple filters."""
    # ?type=IntentCreated&head_id=main
    # Should apply all filters
```

#### 4. CORS and Headers
**Lines**: Throughout

```python
def test_cors_headers_present():
    """Test CORS headers on responses."""
    # Should include Access-Control-Allow-Origin

def test_options_request_handled():
    """Test OPTIONS request for CORS preflight."""
    # OPTIONS /events
    # Should return 200 with CORS headers

def test_content_type_validation():
    """Test API requires application/json."""
    # POST with text/plain
    # Should reject
```

#### 5. Error Responses
**Lines**: Throughout

```python
def test_404_response_format():
    """Test 404 responses are consistent."""
    # GET /nonexistent
    # Should return standard error format

def test_500_response_format():
    """Test 500 responses are consistent."""
    # Internal error
    # Should return error details

def test_validation_error_details():
    """Test 422 responses include field details."""
    # Invalid request body
    # Should specify which fields failed
```

---

## Module: `pathway/models/events.py` (391 lines)

### Currently Tested
- ✅ Basic event envelope creation
- ✅ Event type validation
- ✅ Payload model retrieval

### Missing Tests (Priority: LOW - Core types mostly work)

#### 1. All Event Payload Types
**Lines**: 100-350

```python
def test_all_payload_types_roundtrip():
    """Test each event type's payload can roundtrip through JSON."""
    # For each EventType, create payload, serialize, deserialize
    # Should match original

def test_waypoint_entered_all_fields():
    """Test WaypointEntered with all optional fields."""
    # Full payload with all options

def test_choice_made_payload():
    """Test ChoiceMade payload validation."""
    # Valid choice with options

def test_step_completed_payload():
    """Test StepCompleted payload."""
    # With artifacts, evidence, etc.

def test_blocked_payload_all_categories():
    """Test Blocked payload with each BlockCategory."""
    # Each category and suggested_next

def test_replanned_payload():
    """Test Replanned payload."""
    # New trail version, reason

def test_merged_payload():
    """Test Merged payload."""
    # Multiple branches merged
```

#### 2. Enum Validation
**Lines**: 15-95

```python
def test_event_type_enum_exhaustive():
    """Test all 14 event types are present."""
    # Should have exactly 14 types

def test_actor_kind_values():
    """Test ActorKind enum values."""
    # USER and SYSTEM only

def test_waypoint_kind_values():
    """Test WaypointKind enum values."""
    # All waypoint types

def test_block_category_values():
    """Test BlockCategory enum values."""
    # All blocker categories

def test_artifact_type_values():
    """Test ArtifactType enum values."""
    # CODE, DOC, CONFIG, etc.

def test_side_effects_values():
    """Test SideEffects enum values."""
    # NONE, LOCAL, REMOTE
```

#### 3. Event Envelope Validation
**Lines**: 350-391

```python
def test_event_envelope_required_fields():
    """Test envelope requires session_id, type, etc."""
    # Missing fields should error

def test_event_envelope_optional_fields():
    """Test optional fields can be omitted."""
    # parent_event_id, waypoint_id optional

def test_event_envelope_head_id_defaults():
    """Test head_id defaults to 'main'."""
    # Omit head_id
    # Should default to "main"

def test_event_envelope_get_payload_model_all_types():
    """Test get_payload_model works for all types."""
    # Each EventType should return correct model

def test_event_envelope_invalid_payload():
    """Test get_payload_model with invalid payload."""
    # Payload doesn't match type
    # Should raise validation error
```

---

## Module: `pathway/models/derived.py`

### Currently Tested
- ✅ Basic derived views work
- ❌ Property methods not explicitly tested

### Missing Tests (Priority: MEDIUM)

#### 1. JourneyView Properties
**Lines**: Throughout

```python
def test_journey_view_active_artifacts():
    """Test active_artifacts property."""
    # JourneyView with artifacts
    # Should filter active only

def test_journey_view_branch_count():
    """Test branch counting."""
    # Multiple branches
    # Should count correctly

def test_journey_view_visited_waypoints_unique():
    """Test visited waypoints are unique."""
    # Visit same waypoint twice
    # Should record both visits

def test_journey_view_backtrack_targets():
    """Test backtrack_targets calculation."""
    # Journey with backtrack options
    # Should list valid targets
```

#### 2. LearnedView Properties
**Lines**: Throughout

```python
def test_learned_view_preferences():
    """Test preferences dictionary."""
    # Multiple preferences
    # Should aggregate correctly

def test_learned_view_concepts():
    """Test concepts dictionary."""
    # Concepts with evidence
    # Should track evidence_ids

def test_learned_view_constraints():
    """Test constraints dictionary."""
    # Multiple constraints
    # Should handle updates

def test_learned_view_confidence_ordering():
    """Test learning ordered by confidence."""
    # Sort by confidence
    # Should rank correctly
```

#### 3. ArtifactView Properties
**Lines**: 127-136

```python
def test_artifact_view_active_artifacts():
    """Test active_artifacts property filters."""
    # Mix of active and superseded
    # Should return only active

def test_artifact_view_superseded_artifacts():
    """Test superseded_artifacts property filters."""
    # Mix of active and superseded
    # Should return only superseded

def test_artifact_view_by_waypoint():
    """Test artifacts grouped by waypoint."""
    # Artifacts at different waypoints
    # Should group correctly

def test_artifact_view_by_type():
    """Test artifacts grouped by type."""
    # Mix of CODE, DOC, CONFIG
    # Should group correctly
```

#### 4. SessionState Composite
**Lines**: Throughout

```python
def test_session_state_complete():
    """Test SessionState combines all views."""
    # Full session with all event types
    # Should have journey, learned, artifacts

def test_session_state_event_count():
    """Test event_count is correct."""
    # Various event counts
    # Should match actual count

def test_session_state_serialization():
    """Test SessionState serializes to JSON."""
    # Complex state
    # Should roundtrip through JSON
```

---

## Module: `pathway/store/sqlite_store.py` (401 lines)

### Currently Tested
- ✅ Basic append and get
- ✅ Auto-seq assignment
- ✅ Event ordering
- ✅ Filtering by head, seq range
- ✅ Children and heads queries
- ✅ Session operations

### Missing Tests (Priority: MEDIUM)

#### 1. Concurrency & Race Conditions
**Lines**: 100-186

```python
def test_concurrent_auto_seq_safety():
    """Test auto_seq is thread-safe."""
    # Multiple threads appending simultaneously
    # Seqs should be unique and gapless

def test_concurrent_get_next_seq():
    """Test get_next_seq doesn't skip numbers."""
    # Rapid-fire calls to get_next_seq
    # Should be monotonic

def test_transaction_rollback():
    """Test failed append doesn't corrupt db."""
    # Append that fails mid-transaction
    # DB should remain consistent
```

#### 2. Database Integrity
**Lines**: 65-99

```python
def test_schema_version_tracked():
    """Test schema version is tracked."""
    # Check version metadata table
    # Should record schema version

def test_schema_migration():
    """Test schema can be migrated."""
    # Old schema -> new schema
    # Should preserve data

def test_corrupted_database_handling():
    """Test handling of corrupted database."""
    # Invalid SQLite file
    # Should error gracefully
```

#### 3. Query Optimization
**Lines**: 187-291

```python
def test_get_events_uses_index():
    """Test queries use appropriate indexes."""
    # Large event set
    # Query should be fast

def test_get_events_limit_offset():
    """Test pagination with limit/offset."""
    # Get events with limit and offset
    # Should return correct page

def test_get_events_descending_order():
    """Test events can be retrieved in reverse order."""
    # Newest first
    # Should reverse seq order
```

#### 4. Edge Cases
**Lines**: Throughout

```python
def test_append_event_id_case_sensitive():
    """Test event_id is case-sensitive."""
    # "ABC" vs "abc"
    # Should be different events

def test_session_id_case_sensitive():
    """Test session_id is case-sensitive."""
    # "Session1" vs "session1"
    # Should be different sessions

def test_head_id_special_characters():
    """Test head_id with special chars."""
    # "feature/my-branch"
    # Should work fine

def test_max_event_id_length():
    """Test event_id length limits."""
    # Very long event_id
    # Should handle or reject

def test_empty_payload():
    """Test event with empty payload {}."""
    # Minimal payload
    # Should work

def test_large_payload():
    """Test event with large payload."""
    # 1MB+ JSON payload
    # Should store correctly

def test_unicode_in_payload():
    """Test payload with unicode."""
    # Emoji, foreign chars, etc.
    # Should roundtrip correctly
```

---

## Module: `pathway/store/jsonl_io.py` (157 lines)

### Currently Tested
- ❌ No direct tests exist

### Missing Tests (Priority: HIGH)

#### 1. Export Functionality
**Lines**: 17-48

```python
def test_export_session_jsonl():
    """Test exporting session to JSONL file."""
    # Session with events
    # Should create valid JSONL

def test_export_preserves_order():
    """Test events are exported in seq order."""
    # Export and re-import
    # Order should match

def test_export_preserves_all_fields():
    """Test all event fields are preserved."""
    # Events with all fields
    # Should roundtrip exactly

def test_export_creates_directory():
    """Test export creates output directory if needed."""
    # Output path in non-existent dir
    # Should create dirs

def test_export_overwrites_existing():
    """Test export overwrites existing file."""
    # File exists
    # Should replace it
```

#### 2. Import Functionality
**Lines**: 50-108

```python
def test_import_session_jsonl():
    """Test importing session from JSONL file."""
    # Valid JSONL file
    # Should import all events

def test_import_with_session_override():
    """Test session_id_override replaces IDs."""
    # Import with override
    # All events should use new session_id

def test_import_invalid_json():
    """Test import handles invalid JSON gracefully."""
    # Malformed JSON line
    # Should error on that line

def test_import_missing_fields():
    """Test import handles incomplete events."""
    # Event missing required field
    # Should error clearly

def test_import_duplicate_event_ids():
    """Test import detects duplicate event_ids."""
    # Same event_id twice
    # Should error or skip

def test_import_empty_file():
    """Test import handles empty file."""
    # Empty JSONL
    # Should import 0 events

def test_import_very_large_file():
    """Test import handles large JSONL files."""
    # 10,000+ events
    # Should process efficiently
```

#### 3. Batch Operations
**Lines**: 110-157

```python
def test_export_all_sessions():
    """Test exporting all sessions to directory."""
    # Multiple sessions
    # Should create one file per session

def test_import_all_jsonl_files():
    """Test importing all JSONL files from directory."""
    # Directory with multiple .jsonl
    # Should import all

def test_export_import_roundtrip():
    """Test export then import yields same data."""
    # Export all, import all
    # Should be identical

def test_import_directory_handles_errors():
    """Test import continues on invalid files."""
    # Some valid, some invalid files
    # Should import valid ones
```

---

## Module: `pathway/reducers/journey.py` (166 lines)

### Currently Tested
- ✅ Basic journey reduction
- ✅ Waypoint tracking
- ✅ Branch tips
- ✅ Active head

### Missing Tests (Priority: LOW - Well covered)

#### 1. Helper Functions
**Lines**: 114-166

```python
def test_get_branch_divergence_point():
    """Test finding divergence point between branches."""
    # Two branches diverged
    # Should find common ancestor

def test_get_path_to_waypoint():
    """Test finding path to specific waypoint."""
    # Waypoint in history
    # Should return event sequence

def test_journey_with_no_waypoints():
    """Test journey with only non-navigation events."""
    # Only learning events
    # Should have empty waypoint list

def test_journey_multiple_backtracks():
    """Test journey with multiple backtracks."""
    # Backtrack several times
    # Should track all backtrack targets
```

---

## Module: `pathway/reducers/learned.py` (191 lines)

### Currently Tested
- ✅ Preference learning
- ✅ Concept learning with evidence
- ✅ Confidence clamping
- ✅ Constraint learning

### Missing Tests (Priority: MEDIUM)

#### 1. Helper Functions
**Lines**: 23-26

```python
def test_clamp_function():
    """Test clamp helper function."""
    # Values below, within, above range
    # Should clamp to [0, 1]
```

#### 2. Learning Aggregation
**Lines**: 79-122

```python
def test_multiple_preference_updates():
    """Test preference confidence accumulates."""
    # Multiple PreferenceLearned for same pref
    # Confidence should increase

def test_concept_evidence_tracking():
    """Test concept evidence list grows."""
    # Learn concept multiple times
    # evidence_ids should accumulate

def test_concept_confidence_decay():
    """Test concept confidence can decrease."""
    # Negative confidence_delta
    # Should reduce confidence

def test_constraint_update_replaces():
    """Test constraint updates replace old values."""
    # Learn same constraint twice
    # Second value should win

def test_learned_record_first_seen():
    """Test first_seen_seq is set correctly."""
    # First learning event
    # Should record that seq
```

#### 3. Query Functions
**Lines**: 123-191

```python
def test_get_high_confidence_concepts():
    """Test filtering concepts by confidence threshold."""
    # Mix of high and low confidence
    # Should return only high

def test_get_active_constraints():
    """Test getting all active constraints."""
    # Multiple constraints
    # Should return all

def test_get_user_preferences():
    """Test getting all preferences."""
    # Multiple preferences
    # Should aggregate correctly

def test_summarize_learned():
    """Test summary includes counts."""
    # Full learned view
    # Should count preferences, concepts, constraints
```

---

## Module: `pathway/reducers/artifacts.py` (174 lines)

### Currently Tested
- ✅ Artifact creation
- ✅ Artifact supersedence
- ✅ Active vs superseded filtering
- ✅ Artifact chains

### Missing Tests (Priority: MEDIUM)

#### 1. Helper Functions
**Lines**: 77-156

```python
def test_get_artifact_chain():
    """Test building chain of supersedence."""
    # A supersedes B supersedes C
    # Should return [A, B, C]

def test_get_artifacts_by_type():
    """Test filtering artifacts by ArtifactType."""
    # Mix of CODE, DOC, CONFIG
    # Should filter correctly

def test_get_artifacts_by_waypoint():
    """Test filtering artifacts by waypoint_id."""
    # Artifacts at multiple waypoints
    # Should filter correctly

def test_summarize_artifacts():
    """Test summary includes counts and types."""
    # Mix of artifacts
    # Should count active, superseded, types
```

#### 2. Edge Cases
**Lines**: 21-76

```python
def test_artifact_superseded_by_nonexistent():
    """Test artifact superseded_by points to non-existent artifact."""
    # Dangling superseded_by
    # Should handle gracefully

def test_artifact_circular_supersedence():
    """Test circular supersedence is handled."""
    # A supersedes B supersedes A
    # Should detect or handle

def test_artifact_same_type_different_waypoints():
    """Test same artifact type at different waypoints."""
    # CODE artifact at w1 and w2
    # Should treat as different

def test_artifact_no_evidence():
    """Test artifact with empty evidence list."""
    # Artifact with no evidence
    # Should work fine
```

---

## Module: `pathway/reducers/session.py` (68 lines)

### Currently Tested
- ✅ Full session state reduction

### Missing Tests (Priority: LOW - Orchestration layer)

```python
def test_reduce_session_state_empty():
    """Test reducing empty event list."""
    # No events
    # Should return empty views

def test_reduce_session_state_consistency():
    """Test all views are consistent."""
    # Complex session
    # Journey, learned, artifacts should align

def test_reduce_session_state_performance():
    """Test reduction is efficient."""
    # 10,000+ events
    # Should complete in reasonable time
```

---

## Integration Tests

### Currently Tested
- ✅ Basic API integration
- ✅ API security integration

### Missing Tests (Priority: CRITICAL)

```python
# test_integration_complete.py

def test_full_journey_workflow():
    """Test complete journey from intent to artifacts."""
    # IntentCreated -> TrailVersionCreated -> WaypointEntered -> ... -> ArtifactCreated
    # Full workflow through API

def test_backtrack_and_diverge_workflow():
    """Test backtrack creates new branch."""
    # Forward progress -> Backtrack -> New path
    # Should create branch

def test_learning_persists_across_backtrack():
    """Test learned facts survive backtracking."""
    # Learn on branch -> Backtrack to main -> Check learned
    # Should still have learning

def test_artifact_supersedence_workflow():
    """Test artifact supersedence end-to-end."""
    # Create artifact -> Create superseding artifact
    # Original should be marked superseded

def test_concurrent_api_requests():
    """Test API handles concurrent requests safely."""
    # Multiple clients creating events simultaneously
    # Should not corrupt state

def test_cli_to_api_integration():
    """Test CLI import then API query."""
    # Import via CLI -> Query via API
    # Should see imported data

def test_export_import_roundtrip_via_cli():
    """Test export then import preserves data."""
    # Create via API -> Export via CLI -> Import to new DB -> Verify
    # Should be identical

def test_doctor_on_corrupted_data():
    """Test doctor detects all issue types."""
    # Intentionally corrupt data in various ways
    # Doctor should find each issue

def test_multi_branch_merge():
    """Test merging multiple branches."""
    # Create 3 branches -> Merge all
    # Should handle correctly

def test_replay_determinism():
    """Test replaying same events produces same state."""
    # Reduce twice with same events
    # Should produce identical state
```

---

## Performance & Stress Tests

### Missing Tests (Priority: LOW)

```python
# test_performance.py

def test_large_session_performance():
    """Test performance with 10,000+ events."""
    # Very large session
    # Queries should remain fast

def test_many_sessions_performance():
    """Test performance with 1,000+ sessions."""
    # Many sessions in one database
    # List sessions should be fast

def test_deep_branch_tree_performance():
    """Test performance with deeply nested branches."""
    # 100+ branches
    # Should handle efficiently

def test_memory_usage_large_session():
    """Test memory doesn't balloon with large sessions."""
    # Load large session
    # Memory should be reasonable

def test_database_size_growth():
    """Test database file size scales linearly."""
    # Add 10k events
    # DB size should grow predictably

def test_query_performance_with_indexes():
    """Test indexes improve query performance."""
    # Large dataset
    # Indexed queries should be fast
```

---

## Error Scenarios & Edge Cases

### Missing Tests (Priority: HIGH)

```python
# test_error_scenarios.py

def test_database_locked():
    """Test handling of SQLite database lock."""
    # Two processes accessing db
    # Should handle locks gracefully

def test_disk_full():
    """Test handling when disk is full."""
    # Mock disk full error
    # Should error gracefully

def test_invalid_event_type_in_db():
    """Test handling event type not in enum."""
    # Manually insert invalid type
    # Reducers should handle or skip

def test_invalid_json_in_payload_column():
    """Test handling malformed JSON in db."""
    # Corrupt JSON in database
    # Should error clearly

def test_missing_timestamp():
    """Test event with null timestamp."""
    # ts=NULL in db
    # Should handle or error

def test_max_session_id_length():
    """Test session_id length limits."""
    # Very long session_id
    # Should validate or truncate

def test_max_event_count_per_session():
    """Test session with millions of events."""
    # Very large session
    # Should handle or paginate

def test_reducer_exception_handling():
    """Test reducers handle unexpected data gracefully."""
    # Malformed payload that passes validation
    # Reducer should not crash

def test_unicode_edge_cases():
    """Test unicode edge cases in all fields."""
    # RTL text, emoji, null bytes, etc.
    # Should handle correctly

def test_timezone_handling():
    """Test timestamps with different timezones."""
    # Mix of UTC and local times
    # Should normalize consistently
```

---

## Test Coverage Summary

### Total Tests Needed: ~190 tests

**By Priority:**
- 🔴 **CRITICAL**: 50 tests (CLI commands, integration workflows)
- 🟠 **HIGH**: 60 tests (JSONL I/O, error scenarios, edge cases)
- 🟡 **MEDIUM**: 60 tests (API edge cases, reducer helpers, derived properties)
- 🟢 **LOW**: 20 tests (Performance, rarely-used helpers)

**By Module:**
- `cli.py`: ~60 tests (8 commands with variations)
- `api/main.py`: ~25 tests (edge cases, errors)
- `models/events.py`: ~25 tests (all payload types, enums)
- `models/derived.py`: ~15 tests (properties, serialization)
- `store/sqlite_store.py`: ~20 tests (concurrency, edge cases)
- `store/jsonl_io.py`: ~20 tests (import/export)
- `reducers/*.py`: ~20 tests (helpers, edge cases)
- Integration: ~15 tests (end-to-end workflows)
- Error scenarios: ~20 tests (failure modes)
- Performance: ~10 tests (stress testing)

---

## Implementation Order Recommendation

1. **Week 1**: CLI tests (60 tests) - Critical user interface, most visible functionality
2. **Week 2**: JSONL I/O tests (20 tests) + Integration tests (15 tests) - Complete the user workflows
3. **Week 3**: Error scenarios (20 tests) + API edge cases (25 tests) - Robustness and reliability
4. **Week 4**: Store edge cases (20 tests) + Reducer helpers (20 tests) - Data integrity
5. **Week 5**: Models tests (25 tests) + Performance tests (10 tests) + Polish - Completeness

---

## Notes for Your Coders

### Testing Framework
- All tests should use `pytest`
- Use existing fixtures from `conftest.py`
- For CLI tests, use `subprocess` to call `python -m pathway.cli <command>`
  - Or mock `sys.argv` and call `main()` directly
- For API tests, use `TestClient` from `fastapi.testclient`
- Use `tmp_path` fixture for file operations
- Use in-memory SQLite (`:memory:`) for speed

### CLI Testing Pattern
```python
def test_cli_command():
    """Test a CLI command."""
    # Use tmp_path for database
    db = tmp_path / "test.db"
    
    # Call CLI
    result = subprocess.run(
        ["python", "-m", "pathway.cli", "init", "--db", str(db)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert "Initialized" in result.stdout
```

### API Testing Pattern
```python
def test_api_endpoint(client: TestClient):
    """Test an API endpoint."""
    response = client.post("/events", json={
        "session_id": "test",
        "type": "IntentCreated",
        "payload": {"goal": "test"},
    })
    assert response.status_code == 200
```

### Integration Testing Pattern
```python
def test_workflow():
    """Test complete workflow."""
    # 1. Create via API
    # 2. Query state via API
    # 3. Export via CLI
    # 4. Import to new DB via CLI
    # 5. Verify via API
    # Assert all steps work
```

### Priority Guidelines
- **Focus on CLI first**: Users interact with CLI most
- **Then integration tests**: Ensure workflows work end-to-end
- **Then error scenarios**: Make it robust
- **Then edge cases**: Handle unusual inputs
- **Finally performance**: Ensure it scales

### What to Test
- ✅ **Happy path**: Normal usage
- ✅ **Error cases**: Invalid inputs, missing files, etc.
- ✅ **Edge cases**: Empty data, very large data, unicode, etc.
- ✅ **Concurrency**: Multiple operations simultaneously
- ✅ **Roundtrip**: Export/import, serialize/deserialize
- ✅ **Validation**: All validators catch bad data
- ✅ **Integration**: Full workflows work end-to-end

### What NOT to Test
- ❌ Testing external libraries (FastAPI, Pydantic, SQLite)
- ❌ Testing Python itself
- ❌ Testing implementation details (internal functions unless public API)

### Test Naming
- Use descriptive names: `test_<action>_<scenario>_<expected>`
- Examples:
  - `test_init_creates_database()`
  - `test_import_invalid_jsonl_errors_gracefully()`
  - `test_export_overwrites_existing_file()`

### Documentation
- Every test should have a docstring explaining:
  - What is being tested
  - What scenario is set up
  - What the expected outcome is

---

## Coverage Goals

**Target**: 95%+ coverage across all modules

**Focus areas**:
1. CLI commands (currently 0% tested)
2. JSONL I/O (currently 0% tested)
3. API edge cases (currently ~70% tested)
4. Error handling (currently minimal)
5. Reducer helpers (currently ~60% tested)

**Current estimated coverage**: ~70-75%
- ✅ Strong: API endpoints, core reducers, store operations
- ⚠️ Weak: CLI, JSONL I/O, error scenarios
- ❌ Missing: CLI tests, import/export, error handling

**After implementing these tests**: 95%+ coverage expected

---

## Validation Checklist

After implementing tests, verify:

- [ ] All CLI commands tested with happy path + errors
- [ ] All API endpoints tested with edge cases
- [ ] All event types can roundtrip through JSON
- [ ] All reducers handle empty and invalid inputs
- [ ] All JSONL import/export scenarios covered
- [ ] Concurrency scenarios tested
- [ ] Error scenarios return appropriate codes
- [ ] Integration tests cover full workflows
- [ ] Performance tests establish baselines
- [ ] All tests pass consistently
- [ ] Coverage report shows 95%+

---

## Special Considerations

### Append-Only Architecture
- Tests must respect append-only semantics
- Never modify or delete events in tests
- Backtrack = new event, not deletion

### Event Sourcing
- State is derived from events
- Tests should verify state derivation
- Replaying events should be deterministic

### Branching & Undo
- Tests must cover branch creation
- Verify learning persists across branches
- Test backtrack creates new events

### Security
- Test API key enforcement
- Test session ID validation (no injection)
- Test payload size limits
- Test input sanitization

### Performance
- Pathway should handle 10,000+ events efficiently
- Queries should use indexes
- Memory usage should be bounded

### Data Integrity
- No orphaned events (invalid parent refs)
- Seq numbers must be unique per session
- Event IDs must be globally unique
- Timestamps should be consistent

---

## Remember

- **Test behavior, not implementation**: Focus on what the code does, not how it does it
- **One assertion per test**: Keep tests focused and clear
- **Descriptive names**: Test names should explain the scenario
- **Fast tests**: Use in-memory DB, mock slow operations
- **Independent tests**: Each test should be runnable alone
- **Deterministic tests**: No random values, no time-dependent behavior (unless testing time)
- **Clear failures**: Test failures should point to the issue

Good luck! These tests will make Pathway rock-solid. 🎯
