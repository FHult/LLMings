"""Validation tests for API endpoints."""
import pytest
from app.schemas.session import SessionCreate, CouncilMember
from pydantic import ValidationError


class TestSessionCreateValidation:
    """Test SessionCreate schema validation."""

    def test_valid_session_config(self, sample_session_config):
        """Test valid session configuration passes validation."""
        session = SessionCreate(**sample_session_config)
        assert session.prompt == sample_session_config["prompt"]
        assert len(session.council_members) == 2

    def test_empty_prompt_rejected(self, sample_council_members):
        """Test empty prompt is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(
                prompt="",
                council_members=sample_council_members,
            )
        assert "min_length" in str(exc_info.value).lower()

    def test_prompt_too_long_rejected(self, sample_council_members):
        """Test prompt exceeding max length is rejected."""
        long_prompt = "x" * 60000  # Exceeds 50000 limit
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(
                prompt=long_prompt,
                council_members=sample_council_members,
            )
        assert "max_length" in str(exc_info.value).lower()

    def test_no_chair_rejected(self):
        """Test council without chair is rejected."""
        members = [
            {
                "id": "member-1",
                "provider": "openai",
                "model": "gpt-4",
                "role": "Analyst",
                "is_chair": False,  # No chair
            },
        ]
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(
                prompt="Test prompt",
                council_members=members,
            )
        assert "chair" in str(exc_info.value).lower()

    def test_multiple_chairs_rejected(self):
        """Test council with multiple chairs is rejected."""
        members = [
            {
                "id": "member-1",
                "provider": "openai",
                "model": "gpt-4",
                "role": "Analyst",
                "is_chair": True,
            },
            {
                "id": "member-2",
                "provider": "anthropic",
                "model": "claude-3",
                "role": "Creative",
                "is_chair": True,  # Second chair - invalid
            },
        ]
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(
                prompt="Test prompt",
                council_members=members,
            )
        assert "chair" in str(exc_info.value).lower()

    def test_too_many_iterations_rejected(self, sample_council_members):
        """Test iterations exceeding max is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(
                prompt="Test prompt",
                council_members=sample_council_members,
                iterations=15,  # Exceeds 10 limit
            )
        assert "less than or equal to 10" in str(exc_info.value).lower()

    def test_too_many_council_members_rejected(self):
        """Test too many council members is rejected."""
        # Create 11 members (exceeds 10 limit)
        members = [
            {
                "id": f"member-{i}",
                "provider": "openai",
                "model": "gpt-4",
                "role": f"Member {i}",
                "is_chair": i == 0,
            }
            for i in range(11)
        ]
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(
                prompt="Test prompt",
                council_members=members,
            )
        assert "max_length" in str(exc_info.value).lower()
