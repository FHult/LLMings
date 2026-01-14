"""Test validation constants."""
import pytest
from app.core.validation import (
    MAX_FILE_SIZE,
    MAX_FILE_SIZE_MB,
    MAX_PROMPT_LENGTH,
    MIN_PROMPT_LENGTH,
    MAX_ITERATIONS,
    MIN_ITERATIONS,
    MAX_COUNCIL_MEMBERS,
    MIN_COUNCIL_MEMBERS,
)


class TestValidationConstants:
    """Test validation constants are properly defined."""

    def test_file_size_constants_consistent(self):
        """Test file size constants are consistent."""
        assert MAX_FILE_SIZE == MAX_FILE_SIZE_MB * 1024 * 1024
        assert MAX_FILE_SIZE_MB == 10  # 10MB

    def test_prompt_length_constants(self):
        """Test prompt length constants."""
        assert MIN_PROMPT_LENGTH == 1
        assert MAX_PROMPT_LENGTH == 50000
        assert MIN_PROMPT_LENGTH < MAX_PROMPT_LENGTH

    def test_iteration_constants(self):
        """Test iteration constants."""
        assert MIN_ITERATIONS == 1
        assert MAX_ITERATIONS == 10
        assert MIN_ITERATIONS <= MAX_ITERATIONS

    def test_council_member_constants(self):
        """Test council member constants."""
        assert MIN_COUNCIL_MEMBERS == 1
        assert MAX_COUNCIL_MEMBERS == 10
        assert MIN_COUNCIL_MEMBERS <= MAX_COUNCIL_MEMBERS
