"""Tests for the API key authentication middleware."""

import os

import pytest
from fastapi.testclient import TestClient


def test_no_api_key_required_when_unset(client):
    os.environ.pop("FORGE_API_KEY", None)
    resp = client.get("/api/projects")
    assert resp.status_code == 200


def test_health_always_open(client):
    os.environ["FORGE_API_KEY"] = "test-secret"
    try:
        from backend.app.middleware import API_KEY
        import backend.app.middleware as mw
        mw.API_KEY = "test-secret"

        resp = client.get("/api/health")
        assert resp.status_code == 200
    finally:
        mw.API_KEY = None
        os.environ.pop("FORGE_API_KEY", None)


def test_reject_without_key(client):
    import backend.app.middleware as mw
    mw.API_KEY = "test-secret"
    try:
        resp = client.get("/api/projects")
        assert resp.status_code == 401
        assert "API key" in resp.json()["detail"]
    finally:
        mw.API_KEY = None


def test_accept_with_header(client):
    import backend.app.middleware as mw
    mw.API_KEY = "test-secret"
    try:
        resp = client.get("/api/projects", headers={"X-API-Key": "test-secret"})
        assert resp.status_code == 200
    finally:
        mw.API_KEY = None


def test_accept_with_query_param(client):
    import backend.app.middleware as mw
    mw.API_KEY = "test-secret"
    try:
        resp = client.get("/api/projects?api_key=test-secret")
        assert resp.status_code == 200
    finally:
        mw.API_KEY = None
