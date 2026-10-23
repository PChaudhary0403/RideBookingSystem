"""
pytest configuration and shared fixtures.
"""
import sys
import os

# Ensure the Server directory is on the path so all imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture(autouse=False)
def clean_env(monkeypatch):
    """Ensure SECRET_KEY is always set in tests."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    yield
