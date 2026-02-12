# Contributing to Pathway Core

Thank you for your interest in contributing to Pathway Core! This is an append-only journey engine where undo is navigation and learning persists.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists in [GitHub Issues](https://github.com/mcp-tool-shop-org/pathway/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment (Python version, OS)
   - Sample events or sessions if relevant

### Contributing Code

1. **Fork the repository** and create a branch from `main`
2. **Make your changes**
   - Follow the existing code style
   - Maintain append-only event log semantics
   - Ensure state derivation logic is correct
3. **Test your changes**
   ```bash
   pytest
   ```
4. **Commit your changes**
   - Use clear, descriptive commit messages
   - Reference issue numbers when applicable
5. **Submit a pull request**
   - Describe what your PR does and why
   - Link to related issues

### Development Workflow

```bash
# Clone the repository
git clone https://github.com/mcp-tool-shop-org/pathway.git
cd pathway

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (73 tests covering invariants, API, reducers, store)
pytest

# Test CLI
python -m pathway.cli --help

# Initialize test database
python -m pathway.cli init

# Import sample session
python -m pathway.cli import sample_session.jsonl

# View session state
python -m pathway.cli state sess_001
```

### Architecture

- `pathway/models/` - Pydantic models for events and views
- `pathway/store/` - SQLite event store + JSONL import/export
- `pathway/reducers/` - Compute derived views from events
- `pathway/api/` - FastAPI endpoints
- `pathway/cli.py` - Command-line tools

### Event Types

When adding new features, consider these 14 event types:

| Event Type | Purpose |
|------------|---------|
| IntentCreated | User's goal and context |
| TrailVersionCreated | The learning path/map |
| WaypointEntered | Navigation through trail |
| ChoiceMade | User makes a branching decision |
| StepCompleted | User completes a waypoint |
| Blocked | User hits friction |
| Backtracked | User goes back (undo) |
| Replanned | Trail is revised |
| Merged | Branches converge |
| ArtifactCreated | Output produced |
| ArtifactSuperseded | Old output replaced |
| PreferenceLearned | How user likes to learn |
| ConceptLearned | What user understands |
| ConstraintLearned | User's environment facts |

### Append-Only Semantics

- Events are never edited or deleted
- Undo creates a new event pointing backward
- The original path remains in the log
- Learning survives across backtracking and branches

### Derived Views

The system computes three views from events:

1. **JourneyView** - Current position, branches, visited waypoints
2. **LearnedView** - Preferences, concepts, constraints with confidence scores
3. **ArtifactView** - All outputs with supersedence tracking

### Testing Requirements

- All state derivation logic must have tests
- Test branching and merging scenarios
- Test undo/backtrack behavior
- Test API endpoints with sample events
- Test payload validation and security

### Code Style

- Use type hints with Pydantic models
- Follow PEP 8 conventions
- Keep functions small and focused
- Use descriptive variable names
- Add docstrings for complex functions

### Security

When modifying security features:

- API key validation (`PATHWAY_API_KEY` env var)
- Payload limit enforcement (`PATHWAY_MAX_PAYLOAD_SIZE`)
- Session ID validation (alphanumeric + underscore/hyphen, max 128 chars)

### Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Create git tag: `git tag v0.x.x`
3. Push tag: `git push origin v0.x.x`
4. GitHub Actions will publish to PyPI

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Questions?

Open an issue or start a discussion. We're here to help!

## Related Concepts

- **Undo as navigation** - Not history rewriting, but explicit pointer moves
- **Learning persistence** - Knowledge survives across branches and backtracks
- **First-class branching** - Git-like implicit divergence on new work
- **Honest audit trail** - All paths remain visible in the event log
