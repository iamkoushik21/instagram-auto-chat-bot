"""pytest configuration – set required env vars before any module is imported."""

import os

# Provide dummy credentials so config.py does not raise during test collection
os.environ.setdefault("INSTAGRAM_USERNAME", "test_user")
os.environ.setdefault("INSTAGRAM_PASSWORD", "test_pass")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
