"""
Shared validation constants.
These values should match the frontend VALIDATION constants in frontend/src/lib/config.ts
"""

# File upload limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE_MB = 10

# Prompt limits
MAX_PROMPT_LENGTH = 50000  # 50k characters
MIN_PROMPT_LENGTH = 1

# Session limits
MAX_ITERATIONS = 10
MIN_ITERATIONS = 1
MAX_COUNCIL_MEMBERS = 10
MIN_COUNCIL_MEMBERS = 1
