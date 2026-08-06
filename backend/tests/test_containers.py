"""Tests for the containers and dashboard router."""


class TestListContainers:
    def test_empty_list(self, client):
        resp = client.get("/api/containers")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filter_by_project(self, client, sample_project):
        resp = client.get(f"/api/containers?project_id={sample_project['id']}")
        assert resp.status_code == 200
        assert resp.json() == []


class TestDashboardStats:
    def test_stats_empty(self, client):
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_projects"] == 0
        assert data["total_deployments"] == 0
        assert data["total_containers"] == 0
        assert data["active_tasks"] == 0
        assert data["success_rate"] == 0.0

    def test_stats_with_project(self, client, sample_project):
        resp = client.get("/api/dashboard/stats")
        data = resp.json()
        assert data["total_projects"] == 1
