"""Shared pytest fixtures."""
from __future__ import annotations

import pytest


@pytest.fixture
def client():
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c
