# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-02-27

### Changed
- Promoted to v1.0.0 — production-stable release
- Shipcheck audit pass: SECURITY.md, threat model, structured errors, operator docs

## [0.1.3] - 2026-02-22

### Added
- Initial public release
- Append-only journey engine with event sourcing
- 14 event types covering the full journey lifecycle
- Three derived views: JourneyView, LearnedView, ArtifactView
- FastAPI REST API with session management
- SQLite event store with JSONL import/export
- CLI tools (init, import, state, serve)
- API key protection for write endpoints
- Landing page and translations
