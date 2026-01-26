"""Ontology IDs for Pathway's learned state.

These enums define the canonical identifiers for:
- Preferences: How the user likes to move through learning
- Constraints: Must/must-not facts about the user's environment
- Concepts: Mental model milestones the user is building
"""

from enum import Enum


class PreferenceId(str, Enum):
    """How the user prefers to learn and move through content."""

    # Pacing
    PACE_STEP_SIZE = "pace.step_size"  # tiny | small | medium

    # Explanations
    EXPLANATIONS_DEPTH = "explanations.depth"  # minimal | balanced | deep

    # Learning style
    EXAMPLES_STYLE = "examples.style"  # by_example | by_theory | by_modifying_existing

    # Tolerance for friction
    FRICTION_TOLERANCE = "friction.tolerance"  # low | medium | high

    # How much hand-holding
    AUTONOMY_LEVEL = "autonomy.level"  # guided | collaborative | independent

    # UI preference
    UI_PREFERENCE = "ui.preference"  # cli | web | desktop | unknown


class ConstraintId(str, Enum):
    """Hard constraints about the user's environment and situation."""

    # Environment
    ENVIRONMENT_OS = "environment.os"  # windows | mac | linux | unknown
    ENVIRONMENT_INSTALL_TOLERANCE = "environment.install_tolerance"  # low | medium | high

    # Privacy
    PRIVACY_PUBLIC_SHARING = "privacy.public_sharing"  # boolean

    # Cost
    COST_BUDGET = "cost.budget"  # free_only | low | flexible

    # Time
    TIME_AVAILABLE_PER_SESSION = "time.available_per_session_minutes"  # number

    # Tools
    TOOLS_ALLOWED = "tools.allowed"  # string[]

    # Network
    NETWORK_OFFLINE_OK = "network.offline_ok"  # boolean


class ConceptId(str, Enum):
    """Mental model milestones - what the user understands."""

    # Foundations
    INPUT_OUTPUT = "concept.input_output"
    VARIABLES_AND_TYPES = "concept.variables_and_types"
    CONTROL_FLOW = "concept.control_flow"
    FUNCTIONS = "concept.functions"
    ERRORS_AND_DEBUGGING = "concept.errors_and_debugging"
    FILES_AND_PATHS = "concept.files_and_paths"
    DEPENDENCIES = "concept.dependencies"
    VERSIONING_BASIC = "concept.versioning_basic"

    # App reality
    PROGRAM_ENTRYPOINT = "concept.program_entrypoint"
    CONFIG_VS_CODE = "concept.config_vs_code"
    STATE_VS_STATELESS = "concept.state_vs_stateless"
    REPRODUCIBLE_RUNS = "concept.reproducible_runs"
    PACKAGING_BASIC = "concept.packaging_basic"
    LOGGING_BASIC = "concept.logging_basic"

    # Web basics
    HTTP_REQUEST_RESPONSE = "concept.http_request_response"
    API_BASICS = "concept.api_basics"
    JSON_DATA = "concept.json_data"
    AUTH_BASIC = "concept.auth_basic"

    # Workflow / learning meta-skills
    BACKTRACKING_IS_SAFE = "concept.backtracking_is_safe"
    TRADEOFFS_EXIST = "concept.tradeoffs_exist"
    INCREMENTAL_PROGRESS = "concept.incremental_progress"
    ASKING_GOOD_QUESTIONS = "concept.asking_good_questions"
