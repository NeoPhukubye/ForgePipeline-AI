"""Tests for the deployments router."""

from backend.app.database import get_db


def _insert_deployment(project_id: str, status: str = "LIVE"):
    import uuid

    dep_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            """INSERT INTO deployments (id, project_id, environment, status)
               VALUES (?, ?, 'staging', ?)""",
            (dep_id, project_id, status),
        )
    return dep_id


class TestListDeployments:
    def test_empty_list(self, client):
        resp = client.get("/api/deployments")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filter_by_project(self, client, sample_project):
        _insert_deployment(sample_project["id"])
        resp = client.get(f"/api/deployments?project_id={sample_project['id']}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_filter_by_environment(self, client, sample_project):
        _insert_deployment(sample_project["id"])
        resp = client.get("/api/deployments?environment=staging")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp = client.get("/api/deployments?environment=production")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetDeployment:
    def test_get_existing(self, client, sample_project):
        dep_id = _insert_deployment(sample_project["id"])
        resp = client.get(f"/api/deployments/{dep_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == dep_id

    def test_get_nonexistent(self, client):
        resp = client.get("/api/deployments/nonexistent-id")
        assert resp.status_code == 404


class TestRollback:
    def test_rollback_live_deployment(self, client, sample_project):
        dep_id = _insert_deployment(sample_project["id"], status="LIVE")
        resp = client.post(f"/api/deployments/{dep_id}/rollback")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ROLLED_BACK"

    def test_rollback_non_live_fails(self, client, sample_project):
        dep_id = _insert_deployment(sample_project["id"], status="PENDING")
        resp = client.post(f"/api/deployments/{dep_id}/rollback")
        assert resp.status_code == 400

    def test_rollback_nonexistent(self, client):
        resp = client.post("/api/deployments/nonexistent-id/rollback")
        assert resp.status_code == 404
