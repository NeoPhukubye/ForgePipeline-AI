"""Tests for the execution engine module."""

import pytest

from forgepipeline_ai.execution_engine import ExecutionEngine, ExecutionError
from forgepipeline_ai.planning_agent import DeploymentPlan, PlanStep, StepStatus


class TestURLValidation:
    def test_valid_https_url(self):
        assert ExecutionEngine._validate_repo_url("https://github.com/user/repo.git") is True

    def test_valid_ssh_url(self):
        assert ExecutionEngine._validate_repo_url("git@github.com:user/repo.git") is True

    def test_valid_local_path(self):
        assert ExecutionEngine._validate_repo_url("./my-project") is True

    def test_reject_command_injection_semicolon(self):
        assert ExecutionEngine._validate_repo_url("https://evil.com; rm -rf /") is False

    def test_reject_command_injection_pipe(self):
        assert ExecutionEngine._validate_repo_url("https://evil.com | cat /etc/passwd") is False

    def test_reject_command_injection_ampersand(self):
        assert ExecutionEngine._validate_repo_url("https://evil.com && malicious") is False

    def test_reject_command_injection_backtick(self):
        assert ExecutionEngine._validate_repo_url("`whoami`") is False

    def test_reject_dash_prefix(self):
        assert ExecutionEngine._validate_repo_url("--upload-pack=malicious") is False

    def test_reject_dollar_sign(self):
        assert ExecutionEngine._validate_repo_url("$(evil)") is False

    def test_reject_empty(self):
        assert ExecutionEngine._validate_repo_url("") is False

    def test_reject_newline(self):
        assert ExecutionEngine._validate_repo_url("https://ok.com\nmalicious") is False


class TestDryRun:
    def test_dry_run_does_not_execute(self):
        engine = ExecutionEngine(dry_run=True)
        plan = DeploymentPlan(steps=[
            PlanStep(name="clone_repo", description="Clone", handler="clone_repo", context={"repo_url": "https://github.com/user/app"}),
        ])
        intent = {"source_repo": "https://github.com/user/app"}
        ctx = engine.execute_plan(plan, intent)
        assert plan.steps[0].status == StepStatus.COMPLETED

    def test_dry_run_build_image(self):
        engine = ExecutionEngine(dry_run=True)
        engine.context.repo_path = "/tmp/fake"
        plan = DeploymentPlan(steps=[
            PlanStep(name="build_image", description="Build", handler="build_image"),
        ])
        intent = {"source_repo": "https://github.com/user/app", "environment": "staging"}
        ctx = engine.execute_plan(plan, intent)
        assert plan.steps[0].status == StepStatus.COMPLETED
        assert engine.context.image_name == "app"


class TestErrorRecovery:
    def test_skip_step_on_failed_dependency(self):
        engine = ExecutionEngine(dry_run=True)
        step1 = PlanStep(name="s1", description="Step 1", handler="nonexistent")
        step2 = PlanStep(name="s2", description="Step 2", handler="cleanup", depends_on=["s1"])
        plan = DeploymentPlan(steps=[step1, step2])
        engine.execute_plan(plan, {})
        assert step2.status == StepStatus.SKIPPED

    def test_rollback_on_required_failure(self):
        engine = ExecutionEngine(dry_run=False)
        step = PlanStep(name="analyze_code", description="Analyze", handler="analyze_code", required=True)
        plan = DeploymentPlan(steps=[step])
        ctx = engine.execute_plan(plan, {})
        assert step.status == StepStatus.FAILED
        assert len(ctx.errors) > 0


class TestCallbacks:
    def test_step_callbacks_fire(self):
        engine = ExecutionEngine(dry_run=True)
        started, completed = [], []
        engine.on_step_start(lambda s: started.append(s.name))
        engine.on_step_complete(lambda s: completed.append(s.name))

        plan = DeploymentPlan(steps=[
            PlanStep(name="clone_repo", description="Clone", handler="clone_repo", context={"repo_url": "https://github.com/u/a"}),
        ])
        engine.execute_plan(plan, {"source_repo": "https://github.com/u/a"})
        assert "clone_repo" in started
        assert "clone_repo" in completed
