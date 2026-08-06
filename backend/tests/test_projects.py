"""Tests for the projects router."""


class TestListProjects:
    def test_empty_list(self, client):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_create(self, client, sample_project):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        projects = resp.json()
        assert len(projects) == 1
        assert projects[0]["name"] == "test-app"


class TestCreateProject:
    def test_create_minimal(self, client):
        resp = client.post("/api/projects", json={
            "name": "minimal-app",
            "source_repo_url": "https://github.com/user/app.git",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "minimal-app"
        assert data["environment"] == "staging"
        assert data["id"]

    def test_create_full(self, client):
        resp = client.post("/api/projects", json={
            "name": "full-app",
            "source_repo_url": "https://github.com/user/app.git",
            "cloud_provider": "gcp",
            "deployment_target": "gcp-run",
            "deployment_region": "us-central1",
            "environment": "production",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["cloud_provider"] == "gcp"
        assert data["deployment_region"] == "us-central1"

    def test_create_missing_required_fields(self, client):
        resp = client.post("/api/projects", json={"name": "no-url"})
        assert resp.status_code == 422


class TestGetProject:
    def test_get_existing(self, client, sample_project):
        resp = client.get(f"/api/projects/{sample_project['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "test-app"

    def test_get_nonexistent(self, client):
        resp = client.get("/api/projects/nonexistent-id")
        assert resp.status_code == 404


class TestDeleteProject:
    def test_delete_existing(self, client, sample_project):
        resp = client.delete(f"/api/projects/{sample_project['id']}")
        assert resp.status_code == 204

        resp = client.get(f"/api/projects/{sample_project['id']}")
        assert resp.status_code == 404

    def test_delete_nonexistent(self, client):
        resp = client.delete("/api/projects/nonexistent-id")
        assert resp.status_code == 404
