"""Test fixtures for the FastAPI backend."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    os.environ["FORGE_DB_PATH"] = db_path

    from backend.app.database import init_db

    init_db()
    yield
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def client():
    from backend.app.main import app

    return TestClient(app)


@pytest.fixture
def sample_project(client):
    resp = client.post(
        "/api/projects",
        json={
            "name": "test-app",
            "source_repo_url": "https://github.com/user/test-app.git",
            "cloud_provider": "aws",
            "deployment_target": "aws-ecs",
            "environment": "staging",
        },
    )
    assert resp.status_code == 201
    return resp.json()
