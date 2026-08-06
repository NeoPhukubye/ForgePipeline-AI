"""Tests for the tasks router."""


class TestListTasks:
    def test_empty_list(self, client):
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filter_by_project_id(self, client, sample_project):
        resp = client.post("/api/tasks/deploy", json={
            "project_id": sample_project["id"],
            "task_type": "ANALYZE",
            "dry_run": True,
        })
        assert resp.status_code == 202

        resp = client.get(f"/api/tasks?project_id={sample_project['id']}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_filter_by_status(self, client, sample_project):
        client.post("/api/tasks/deploy", json={
            "project_id": sample_project["id"],
            "dry_run": True,
        })
        resp = client.get("/api/tasks?status=PENDING")
        assert resp.status_code == 200


class TestTriggerDeploy:
    def test_trigger_deploy(self, client, sample_project):
        resp = client.post("/api/tasks/deploy", json={
            "project_id": sample_project["id"],
            "task_type": "DEPLOY",
            "dry_run": True,
        })
        assert resp.status_code == 202
        data = resp.json()
        assert data["task_type"] == "DEPLOY"
        assert data["status"] == "PENDING"
        assert data["project_id"] == sample_project["id"]

    def test_trigger_containerize(self, client, sample_project):
        resp = client.post("/api/tasks/deploy", json={
            "project_id": sample_project["id"],
            "task_type": "CONTAINERIZE",
            "dry_run": True,
        })
        assert resp.status_code == 202
        assert resp.json()["task_type"] == "CONTAINERIZE"

    def test_trigger_nonexistent_project(self, client):
        resp = client.post("/api/tasks/deploy", json={
            "project_id": "nonexistent",
            "task_type": "DEPLOY",
        })
        assert resp.status_code == 404


class TestGetTask:
    def test_get_existing(self, client, sample_project):
        create_resp = client.post("/api/tasks/deploy", json={
            "project_id": sample_project["id"],
            "dry_run": True,
        })
        task_id = create_resp.json()["id"]

        resp = client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == task_id

    def test_get_nonexistent(self, client):
        resp = client.get("/api/tasks/nonexistent-id")
        assert resp.status_code == 404


class TestGetTaskLogs:
    def test_get_logs_empty(self, client, sample_project):
        create_resp = client.post("/api/tasks/deploy", json={
            "project_id": sample_project["id"],
            "dry_run": True,
        })
        task_id = create_resp.json()["id"]

        resp = client.get(f"/api/tasks/{task_id}/logs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
