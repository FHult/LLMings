"""Tests for the new CouncilMember validators added in the second code-review pass.

Covers:
- provider field validator (unknown provider rejected at parse time)
- custom_personality max_length constraint
"""
import pytest
from pydantic import ValidationError

from app.schemas.session import CouncilMember, SessionCreate
from app.core.validation import MAX_PROMPT_LENGTH


def _base_member(**overrides) -> dict:
    return {
        "id": "m1",
        "provider": "openai",
        "model": "gpt-4",
        "role": "Analyst",
        "is_chair": True,
        **overrides,
    }


class TestProviderValidator:
    @pytest.mark.parametrize("provider", ["openai", "anthropic", "google", "grok", "ollama"])
    def test_all_known_providers_accepted(self, provider):
        member = CouncilMember(**_base_member(provider=provider))
        assert member.provider == provider

    @pytest.mark.parametrize("provider", [
        "unknown", "azure", "mistral", "cohere", "OPENAI", "Open AI", "", "  ",
    ])
    def test_unknown_provider_rejected(self, provider):
        with pytest.raises(ValidationError) as exc_info:
            CouncilMember(**_base_member(provider=provider))
        error_str = str(exc_info.value).lower()
        assert "provider" in error_str or "unknown" in error_str

    def test_error_message_lists_valid_providers(self):
        """The rejection message must name the valid providers so callers know
        what to use — prevents cryptic 422 responses in production."""
        with pytest.raises(ValidationError) as exc_info:
            CouncilMember(**_base_member(provider="azure"))
        msg = str(exc_info.value)
        for valid in ["openai", "anthropic", "google", "grok", "ollama"]:
            assert valid in msg

    def test_unknown_provider_rejected_in_session_create(self, sample_council_members):
        """The validator fires inside a full SessionCreate, not just CouncilMember."""
        members = [
            {**sample_council_members[0], "provider": "unknown_cloud"},
            sample_council_members[1],
        ]
        with pytest.raises(ValidationError):
            SessionCreate(
                prompt="Test prompt",
                council_members=members,
            )


class TestCustomPersonalityLength:
    def test_none_accepted(self):
        member = CouncilMember(**_base_member(custom_personality=None))
        assert member.custom_personality is None

    def test_short_personality_accepted(self):
        member = CouncilMember(**_base_member(custom_personality="Be concise."))
        assert member.custom_personality == "Be concise."

    def test_at_exact_limit_accepted(self):
        at_limit = "x" * MAX_PROMPT_LENGTH
        member = CouncilMember(**_base_member(custom_personality=at_limit))
        assert len(member.custom_personality) == MAX_PROMPT_LENGTH

    def test_one_over_limit_rejected(self):
        over_limit = "x" * (MAX_PROMPT_LENGTH + 1)
        with pytest.raises(ValidationError) as exc_info:
            CouncilMember(**_base_member(custom_personality=over_limit))
        # Pydantic v2 reports this as string_too_long, not max_length
        assert "string_too_long" in str(exc_info.value).lower() or "50000" in str(exc_info.value)

    def test_very_long_personality_rejected(self):
        """A multi-megabyte string must be rejected before reaching the orchestrator."""
        gigantic = "x" * (MAX_PROMPT_LENGTH * 2)
        with pytest.raises(ValidationError):
            CouncilMember(**_base_member(custom_personality=gigantic))
