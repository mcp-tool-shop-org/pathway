"""Tests for API security features.

Tests:
1. API key requirement (when PATHWAY_API_KEY is set)
2. Payload size limit
3. Session ID validation
"""

import pytest
from fastapi.testclient import TestClient

from pathway.api.main import create_app
from pathway.models.events import EventType


@pytest.fixture
def client():
    """Create a test client without API key requirement."""
    app = create_app(":memory:", require_api_key=False)
    return TestClient(app)


@pytest.fixture
def client_with_api_key(monkeypatch):
    """Create a test client WITH API key requirement."""
    monkeypatch.setenv("PATHWAY_API_KEY", "test-secret-key")
    app = create_app(":memory:", require_api_key=True)
    return TestClient(app)


class TestAPIKeyAuthentication:
    """Test API key authentication."""

    def test_no_api_key_required_by_default(self, client):
        """When no API key is configured, writes should work."""
        response = client.post(
            "/events",
            json={
                "session_id": "test_sess",
                "type": EventType.INTENT_CREATED.value,
                "payload": {"goal": "test"},
            },
        )
        assert response.status_code == 200

    def test_api_key_required_when_configured(self, client_with_api_key):
        """When API key is set, requests without it should fail."""
        response = client_with_api_key.post(
            "/events",
            json={
                "session_id": "test_sess",
                "type": EventType.INTENT_CREATED.value,
                "payload": {"goal": "test"},
            },
        )
        assert response.status_code == 401
        assert "API key" in response.json()["detail"]

    def test_api_key_invalid(self, client_with_api_key):
        """Wrong API key should fail."""
        response = client_with_api_key.post(
            "/events",
            json={
                "session_id": "test_sess",
                "type": EventType.INTENT_CREATED.value,
                "payload": {"goal": "test"},
            },
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401

    def test_api_key_valid(self, client_with_api_key):
        """Correct API key should succeed."""
        response = client_with_api_key.post(
            "/events",
            json={
                "session_id": "test_sess",
                "type": EventType.INTENT_CREATED.value,
                "payload": {"goal": "test"},
            },
            headers={"X-API-Key": "test-secret-key"},
        )
        assert response.status_code == 200

    def test_read_endpoints_dont_require_api_key(self, client_with_api_key):
        """GET endpoints should work without API key (read-only)."""
        # First create a session with valid key
        client_with_api_key.post(
            "/events",
            json={
                "session_id": "test_sess",
                "type": EventType.INTENT_CREATED.value,
                "payload": {"goal": "test"},
            },
            headers={"X-API-Key": "test-secret-key"},
        )

        # Read without API key should work
        response = client_with_api_key.get("/sessions")
        assert response.status_code == 200


class TestSessionIDValidation:
    """Test session_id format validation."""

    def test_valid_session_ids(self, client):
        """Valid session IDs should be accepted."""
        valid_ids = [
            "test",
            "test_session",
            "test-session",
            "TestSession123",
            "a" * 128,  # Max length
            "session_2024_01_15",
        ]
        for session_id in valid_ids:
            response = client.post(
                "/events",
                json={
                    "session_id": session_id,
                    "type": EventType.INTENT_CREATED.value,
                    "payload": {"goal": "test"},
                },
            )
            assert response.status_code == 200, f"Failed for: {session_id}"

    def test_invalid_session_id_special_chars(self, client):
        """Session IDs with special characters should be rejected."""
        invalid_ids = [
            "test session",  # space
            "test;session",  # semicolon (SQL injection)
            "test'session",  # quote
            'test"session',  # double quote
            "test/session",  # slash
            "test\\session",  # backslash
            "../etc/passwd",  # path traversal
        ]
        for session_id in invalid_ids:
            response = client.post(
                "/events",
                json={
                    "session_id": session_id,
                    "type": EventType.INTENT_CREATED.value,
                    "payload": {"goal": "test"},
                },
            )
            assert response.status_code == 422, f"Should reject: {session_id}"

    def test_invalid_session_id_too_long(self, client):
        """Session IDs over 128 chars should be rejected."""
        response = client.post(
            "/events",
            json={
                "session_id": "a" * 129,
                "type": EventType.INTENT_CREATED.value,
                "payload": {"goal": "test"},
            },
        )
        assert response.status_code == 422

    def test_invalid_session_id_empty(self, client):
        """Empty session IDs should be rejected."""
        response = client.post(
            "/events",
            json={
                "session_id": "",
                "type": EventType.INTENT_CREATED.value,
                "payload": {"goal": "test"},
            },
        )
        assert response.status_code == 422

    def test_session_id_validated_on_get(self, client):
        """Session ID should be validated on GET endpoints too."""
        response = client.get("/session/test;DROP TABLE events/state")
        assert response.status_code == 400
        assert "Invalid session_id" in response.json()["detail"]


class TestPayloadSizeLimit:
    """Test payload size limits."""

    def test_normal_payload_accepted(self, client):
        """Normal-sized payloads should be accepted."""
        response = client.post(
            "/events",
            json={
                "session_id": "test_sess",
                "type": EventType.INTENT_CREATED.value,
                "payload": {"goal": "test", "data": "x" * 1000},
            },
        )
        assert response.status_code == 200

    def test_large_payload_rejected(self):
        """Payloads over the limit should be rejected."""
        # Create a new client with a small payload limit for testing
        app = create_app(":memory:", require_api_key=False, max_payload_size=100)
        small_limit_client = TestClient(app)

        response = small_limit_client.post(
            "/events",
            json={
                "session_id": "test_sess",
                "type": EventType.INTENT_CREATED.value,
                "payload": {"goal": "test", "data": "x" * 1000},
            },
        )
        assert response.status_code == 413
        assert "Payload too large" in response.json()["detail"]
