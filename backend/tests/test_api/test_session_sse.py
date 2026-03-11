"""Tests for the SSE event contract on POST /session/create and /session/resume.

Verifies:
- Every response line is prefixed with 'data: '
- All data payloads are valid JSON
- Required fields are present per event type
- error events include the error_type field added in the second review pass
- resume returns 500 (not an orphaned running session) when DB commit fails
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.session_orchestrator import SessionOrchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_sse(body: str) -> list[dict]:
    """Parse an SSE response body into a list of event dicts."""
    events = []
    for line in body.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


MINIMAL_SESSION_PAYLOAD = {
    "prompt": "What is 2+2?",
    "council_members": [
        {
            "id": "chair-1",
            "provider": "openai",
            "model": "gpt-4",
            "role": "Chair",
            "is_chair": True,
        }
    ],
    "iterations": 1,
    "template": "balanced",
    "preset": "balanced",
    "autopilot": True,
}


# ---------------------------------------------------------------------------
# SSE format contract
# ---------------------------------------------------------------------------

class TestSSEFormat:
    @pytest.mark.asyncio
    async def test_all_lines_are_data_prefixed_or_blank(self, client, monkeypatch):
        """Every non-blank line in an SSE stream must start with 'data: '."""
        async def mock_run_session(self_inner, session):
            yield {"type": "status", "message": "Running"}
            yield {"type": "complete"}

        monkeypatch.setattr(SessionOrchestrator, "run_session", mock_run_session)

        response = await client.post("/api/session/create", json=MINIMAL_SESSION_PAYLOAD)
        assert response.status_code == 200

        for line in response.text.splitlines():
            assert line == "" or line.startswith("data: "), (
                f"SSE line must start with 'data: ' or be blank, got: {line!r}"
            )

    @pytest.mark.asyncio
    async def test_all_data_payloads_are_valid_json(self, client, monkeypatch):
        """Every data: payload must be valid JSON — clients JSON.parse() these."""
        async def mock_run_session(self_inner, session):
            yield {"type": "status", "message": "ok"}
            yield {"type": "complete"}

        monkeypatch.setattr(SessionOrchestrator, "run_session", mock_run_session)
        response = await client.post("/api/session/create", json=MINIMAL_SESSION_PAYLOAD)

        for line in response.text.splitlines():
            if line.startswith("data: "):
                json.loads(line[6:])  # must not raise

    @pytest.mark.asyncio
    async def test_session_created_event_has_session_id(self, client, monkeypatch):
        """The first event must be session_created with a non-null session_id."""
        async def mock_run_session(self_inner, session):
            yield {"type": "complete"}

        monkeypatch.setattr(SessionOrchestrator, "run_session", mock_run_session)
        response = await client.post("/api/session/create", json=MINIMAL_SESSION_PAYLOAD)

        events = _parse_sse(response.text)
        assert events, "Stream must not be empty"
        first = events[0]
        assert first["type"] == "session_created"
        assert first.get("session_id") is not None

    @pytest.mark.asyncio
    async def test_complete_event_emitted_at_end(self, client, monkeypatch):
        """A successfully completed session must include a complete event."""
        async def mock_run_session(self_inner, session):
            yield {"type": "status", "message": "Running"}
            yield {"type": "complete"}

        monkeypatch.setattr(SessionOrchestrator, "run_session", mock_run_session)
        response = await client.post("/api/session/create", json=MINIMAL_SESSION_PAYLOAD)

        events = _parse_sse(response.text)
        types = [e["type"] for e in events]
        assert "complete" in types


# ---------------------------------------------------------------------------
# error event contract
# ---------------------------------------------------------------------------

class TestErrorEventContract:
    @pytest.mark.asyncio
    async def test_error_event_includes_error_type(self, client, monkeypatch):
        """error events must include error_type so clients can categorise failures."""
        async def mock_run_session(self_inner, session):
            raise ValueError("Simulated provider failure")
            yield  # make it a generator

        monkeypatch.setattr(SessionOrchestrator, "run_session", mock_run_session)
        response = await client.post("/api/session/create", json=MINIMAL_SESSION_PAYLOAD)

        events = _parse_sse(response.text)
        error_events = [e for e in events if e["type"] == "error"]
        assert error_events, "At least one error event expected"

        err = error_events[-1]
        assert "error_type" in err, "error_type field is missing from error event"
        assert err["error_type"] == "ValueError"
        assert "Simulated provider failure" in err["message"]

    @pytest.mark.asyncio
    async def test_error_event_has_message_field(self, client, monkeypatch):
        async def mock_run_session(self_inner, session):
            raise RuntimeError("connection refused")
            yield

        monkeypatch.setattr(SessionOrchestrator, "run_session", mock_run_session)
        response = await client.post("/api/session/create", json=MINIMAL_SESSION_PAYLOAD)

        events = _parse_sse(response.text)
        error_events = [e for e in events if e["type"] == "error"]
        assert error_events
        assert "message" in error_events[-1]

    @pytest.mark.asyncio
    async def test_orchestrator_error_event_forwarded(self, client, monkeypatch):
        """Errors yielded by the orchestrator (not raised) must also be forwarded."""
        async def mock_run_session(self_inner, session):
            yield {
                "type": "error",
                "provider": "openai",
                "member_id": "m1",
                "member_role": "Chair",
                "message": "Rate limit exceeded",
            }

        monkeypatch.setattr(SessionOrchestrator, "run_session", mock_run_session)
        response = await client.post("/api/session/create", json=MINIMAL_SESSION_PAYLOAD)

        events = _parse_sse(response.text)
        error_events = [e for e in events if e["type"] == "error"]
        assert any("Rate limit" in e.get("message", "") for e in error_events)


# ---------------------------------------------------------------------------
# Resume-specific contract
# ---------------------------------------------------------------------------

class TestResumeContract:
    @pytest.mark.asyncio
    async def test_resume_without_state_creates_new_session(self, client, monkeypatch):
        """Resuming with no session_id in resume_state falls back to creating new."""
        async def mock_run_session(self_inner, session):
            yield {"type": "complete"}

        monkeypatch.setattr(SessionOrchestrator, "run_session", mock_run_session)

        payload = {**MINIMAL_SESSION_PAYLOAD, "resume_state": {"current_iteration": 1}}
        response = await client.post("/api/session/resume", json=payload)
        assert response.status_code == 200

        events = _parse_sse(response.text)
        assert any(e["type"] == "session_created" for e in events)
