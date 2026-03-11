"""Tests for SessionOrchestrator._collect_from_members.

Focuses on:
- Exactly one DB commit for N successful members (batch, not per-response)
- Error isolation: a failing provider yields an error event but does not
  prevent successful members from being saved
- Empty member list yields nothing
"""
import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.session import Session
from app.schemas.session import SessionCreate, CouncilMember
from app.services.session_orchestrator import SessionOrchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(members: list[dict]) -> SessionCreate:
    return SessionCreate(
        prompt="Test prompt",
        council_members=[CouncilMember(**m) for m in members],
        iterations=1,
    )


async def _drain(gen) -> list[dict]:
    """Collect all events from an async generator."""
    events = []
    async for event in gen:
        events.append(event)
    return events


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def session(test_db):
    """Insert a minimal Session row so FK constraints on Response are satisfied."""
    row = Session(
        id=str(uuid.uuid4()),
        prompt="Test prompt",
        chair_provider="openai",
        total_iterations=1,
        current_iteration=1,
        merge_template="balanced",
        preset="balanced",
        status="running",
        autopilot=False,
    )
    test_db.add(row)
    await test_db.commit()
    return row


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCollectFromMembersCommit:
    @pytest.mark.asyncio
    async def test_two_members_one_commit(self, test_db, session):
        """Two successful members must produce exactly one DB commit."""
        commit_count = 0
        original_commit = test_db.commit

        async def counting_commit():
            nonlocal commit_count
            commit_count += 1
            await original_commit()

        config = _make_config([
            {"id": "m1", "provider": "openai", "model": "gpt-4", "role": "A", "is_chair": True},
            {"id": "m2", "provider": "anthropic", "model": "claude-3", "role": "B"},
        ])

        orchestrator = SessionOrchestrator(test_db)
        orchestrator._init_state_from_config(config)
        test_db.commit = counting_commit

        orchestrator._get_provider_response = AsyncMock(
            return_value=("Response text", 50, 100, 0.001)
        )
        mock_provider = MagicMock()
        orchestrator.provider_factory.get_provider = MagicMock(return_value=mock_provider)

        events = await _drain(
            orchestrator._collect_from_members(
                session, list(orchestrator.council_members), "Test", 1, "initial_response"
            )
        )

        assert commit_count == 1, "Expected exactly one batch commit for 2 members"
        response_events = [e for e in events if e["type"] == "initial_response"]
        assert len(response_events) == 2

    @pytest.mark.asyncio
    async def test_event_contains_response_id_before_commit(self, test_db, session):
        """response_id must be present in the event even before commit completes."""
        commit_called_after_yield = False
        events_seen: list[dict] = []
        original_commit = test_db.commit

        async def late_commit():
            nonlocal commit_called_after_commit
            commit_called_after_commit = True
            await original_commit()

        commit_called_after_commit = False
        config = _make_config([
            {"id": "m1", "provider": "openai", "model": "gpt-4", "role": "A", "is_chair": True},
        ])

        orchestrator = SessionOrchestrator(test_db)
        orchestrator._init_state_from_config(config)
        test_db.commit = late_commit
        orchestrator._get_provider_response = AsyncMock(
            return_value=("content", 10, 20, 0.0)
        )
        mock_provider = MagicMock()
        orchestrator.provider_factory.get_provider = MagicMock(return_value=mock_provider)

        async for event in orchestrator._collect_from_members(
            session, list(orchestrator.council_members), "Test", 1, "initial_response"
        ):
            events_seen.append(event)
            # When the event is yielded, commit has NOT happened yet
            if event["type"] == "initial_response":
                assert not commit_called_after_commit, (
                    "Commit must happen AFTER yielding the event, not before"
                )

        assert commit_called_after_commit, "Commit must happen at end of loop"
        assert events_seen[0]["response_id"] is not None

    @pytest.mark.asyncio
    async def test_failed_member_yields_error_event_others_committed(self, test_db, session):
        """One failing provider must yield an error event but not prevent
        the successful member's response from being committed."""
        commit_count = 0
        original_commit = test_db.commit

        async def counting_commit():
            nonlocal commit_count
            commit_count += 1
            await original_commit()

        config = _make_config([
            {"id": "m1", "provider": "openai", "model": "gpt-4", "role": "A", "is_chair": True},
            {"id": "m2", "provider": "anthropic", "model": "claude-3", "role": "B"},
        ])

        orchestrator = SessionOrchestrator(test_db)
        orchestrator._init_state_from_config(config)
        test_db.commit = counting_commit

        call_count = 0

        async def provider_response(provider, prompt, temp, personality, model, think):
            nonlocal call_count
            call_count += 1
            if model == "gpt-4":
                raise ValueError("Simulated API failure")
            return ("Good response", 50, 100, 0.001)

        orchestrator._get_provider_response = provider_response
        mock_provider = MagicMock()
        orchestrator.provider_factory.get_provider = MagicMock(return_value=mock_provider)

        events = await _drain(
            orchestrator._collect_from_members(
                session, list(orchestrator.council_members), "Test", 1, "initial_response"
            )
        )

        error_events = [e for e in events if e["type"] == "error"]
        success_events = [e for e in events if e["type"] == "initial_response"]

        assert len(error_events) == 1, "One provider failed → one error event"
        assert len(success_events) == 1, "One provider succeeded → one response event"
        assert commit_count == 1, "Successful response must still be committed"
        assert "gpt-4" in error_events[0]["message"] or error_events[0]["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_empty_member_list_yields_nothing(self, test_db, session):
        """No members → generator yields nothing and no DB commit happens."""
        commit_count = 0
        original_commit = test_db.commit

        async def counting_commit():
            nonlocal commit_count
            commit_count += 1
            await original_commit()

        config = _make_config([
            {"id": "m1", "provider": "openai", "model": "gpt-4", "role": "A", "is_chair": True},
        ])
        orchestrator = SessionOrchestrator(test_db)
        orchestrator._init_state_from_config(config)
        test_db.commit = counting_commit

        events = await _drain(
            orchestrator._collect_from_members(session, [], "Test", 1, "initial_response")
        )

        assert events == []
        assert commit_count == 0

    @pytest.mark.asyncio
    async def test_all_members_fail_no_commit(self, test_db, session):
        """If every provider fails, nothing is committed."""
        commit_count = 0
        original_commit = test_db.commit

        async def counting_commit():
            nonlocal commit_count
            commit_count += 1
            await original_commit()

        config = _make_config([
            {"id": "m1", "provider": "openai", "model": "gpt-4", "role": "A", "is_chair": True},
        ])
        orchestrator = SessionOrchestrator(test_db)
        orchestrator._init_state_from_config(config)
        test_db.commit = counting_commit

        async def always_fail(provider, prompt, temp, personality, model, think):
            raise RuntimeError("Network error")

        orchestrator._get_provider_response = always_fail
        orchestrator.provider_factory.get_provider = MagicMock(return_value=MagicMock())

        events = await _drain(
            orchestrator._collect_from_members(
                session, list(orchestrator.council_members), "Test", 1, "initial_response"
            )
        )

        error_events = [e for e in events if e["type"] == "error"]
        assert len(error_events) == 1
        assert commit_count == 0, "No commit when no responses to save"
