"""
Execution engine that carries out deployment plan steps with proper
state management, error recovery, rollback support, and real operations.
"""

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .analyzer import AnalysisResult, CodeAnalyzer
from .dockerfile_generator import DockerfileGenerator
from .planning_agent import DeploymentPlan, PlanStep, StepStatus


@dataclass
class ExecutionContext:
    repo_path: str | None = None
    analysis: AnalysisResult | None = None
    image_name: str | None = None
    image_tag: str | None = None
    registry_url: str | None = None
    dockerfile_content: str | None = None
    deployed_url: str | None = None
    errors: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def full_image_ref(self) -> str | None:
        if not self.image_name:
            return None
        tag = self.image_tag or "latest"
        if self.registry_url:
            return f"{self.registry_url}/{self.image_name}:{tag}"
        return f"{self.image_name}:{tag}"


class ExecutionError(Exception):
    def __init__(self, step_name: str, message: str, recoverable: bool = True):
        self.step_name = step_name
        self.recoverable = recoverable
        super().__init__(f"[{step_name}] {message}")


class ExecutionEngine:
    """Executes deployment plans with state tracking and error recovery."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.context = ExecutionContext()
        self._handlers: dict[str, Callable] = {
            "clone_repo": self._handle_clone_repo,
            "analyze_code": self._handle_analyze_code,
            "generate_dockerfile": self._handle_generate_dockerfile,
            "validate_dockerfile": self._handle_validate_dockerfile,
            "build_image": self._handle_build_image,
            "push_image": self._handle_push_image,
            "deploy_ecs_configure": self._handle_deploy_ecs_configure,
            "deploy_ecs": self._handle_deploy_ecs,
            "deploy_cloud_run": self._handle_deploy_cloud_run,
            "deploy_lambda_package": self._handle_deploy_lambda_package,
            "deploy_lambda": self._handle_deploy_lambda,
            "deploy_k8s_generate": self._handle_deploy_k8s_generate,
            "deploy_k8s_apply": self._handle_deploy_k8s_apply,
            "deploy_azure_container_apps": self._handle_deploy_azure,
            "deploy_generic": self._handle_deploy_generic,
            "health_check": self._handle_health_check,
            "cleanup": self._handle_cleanup,
        }
        self._on_step_start: Callable[[PlanStep], None] | None = None
        self._on_step_complete: Callable[[PlanStep], None] | None = None
        self._on_step_fail: Callable[[PlanStep, Exception], None] | None = None

    def on_step_start(self, callback: Callable[[PlanStep], None]):
        self._on_step_start = callback

    def on_step_complete(self, callback: Callable[[PlanStep], None]):
        self._on_step_complete = callback

    def on_step_fail(self, callback: Callable[[PlanStep, Exception], None]):
        self._on_step_fail = callback

    def execute_plan(self, plan: DeploymentPlan, intent: dict) -> ExecutionContext:
        for step in plan.steps:
            if self._should_skip(step, plan):
                step.status = StepStatus.SKIPPED
                continue

            step.status = StepStatus.RUNNING
            if self._on_step_start:
                self._on_step_start(step)

            try:
                self._execute_step(step, intent)
                step.status = StepStatus.COMPLETED
                if self._on_step_complete:
                    self._on_step_complete(step)
            except ExecutionError as e:
                step.status = StepStatus.FAILED
                self.context.errors.append(str(e))

                if self._on_step_fail:
                    self._on_step_fail(step, e)

                if e.recoverable and step.retry_count < step.max_retries:
                    step.retry_count += 1
                    step.status = StepStatus.RUNNING
                    try:
                        self._execute_step(step, intent)
                        step.status = StepStatus.COMPLETED
                    except ExecutionError:
                        step.status = StepStatus.FAILED
                        if step.required:
                            self._rollback(plan)
                            break
                elif step.required:
                    self._rollback(plan)
                    break
            except Exception as e:
                step.status = StepStatus.FAILED
                self.context.errors.append(f"Unexpected error in {step.name}: {e}")
                if step.required:
                    self._rollback(plan)
                    break

        return self.context

    def _should_skip(self, step: PlanStep, plan: DeploymentPlan) -> bool:
        for dep_name in step.depends_on:
            dep_step = next((s for s in plan.steps if s.name == dep_name), None)
            if dep_step and dep_step.status == StepStatus.FAILED:
                return True
        return False

    def _execute_step(self, step: PlanStep, intent: dict):
        handler = self._handlers.get(step.handler)
        if not handler:
            raise ExecutionError(step.name, f"No handler for: {step.handler}", recoverable=False)
        handler(step, intent)

    def _rollback(self, plan: DeploymentPlan):
        if self.context.repo_path and os.path.exists(self.context.repo_path):
            shutil.rmtree(self.context.repo_path, ignore_errors=True)

    def _run_cmd(self, cmd: list[str], cwd: str | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
        if self.dry_run:
            return subprocess.CompletedProcess(cmd, 0, stdout="[dry-run]", stderr="")

        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            env=run_env,
            timeout=300,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return result

    # --- Step Handlers ---

    @staticmethod
    def _validate_repo_url(url: str) -> bool:
        """Reject URLs that could be used for command injection or local file access."""
        if not url:
            return False
        url_stripped = url.strip()
        if url_stripped.startswith("-"):
            return False
        if any(c in url_stripped for c in [";", "|", "&", "$", "`", "\n", "\r"]):
            return False
        import re
        valid = (
            re.match(r"^https?://[\w.\-/~@:]+$", url_stripped)
            or re.match(r"^git@[\w.\-]+:[\w.\-/]+$", url_stripped)
            or re.match(r"^[\w.\-/\\]+$", url_stripped)
        )
        return bool(valid)

    def _handle_clone_repo(self, step: PlanStep, intent: dict):
        repo_url = intent.get("source_repo") or step.context.get("repo_url")
        if not repo_url:
            raise ExecutionError(step.name, "No source repository URL provided", recoverable=False)

        if not self._validate_repo_url(repo_url):
            raise ExecutionError(step.name, f"Invalid or unsafe repository URL: {repo_url}", recoverable=False)

        self.context.repo_path = tempfile.mkdtemp(prefix="forge_")
        try:
            self._run_cmd(["git", "clone", "--depth", "1", repo_url, self.context.repo_path])
        except subprocess.CalledProcessError as e:
            raise ExecutionError(step.name, f"Failed to clone: {e.stderr}")
        except FileNotFoundError:
            raise ExecutionError(step.name, "git is not installed", recoverable=False)

    def _handle_analyze_code(self, step: PlanStep, intent: dict):
        if not self.context.repo_path:
            raise ExecutionError(step.name, "No repository to analyze", recoverable=False)

        analyzer = CodeAnalyzer()
        self.context.analysis = analyzer.analyze(self.context.repo_path)
        self.context.artifacts["analysis"] = self.context.analysis.to_dict()

    def _handle_generate_dockerfile(self, step: PlanStep, intent: dict):
        if not self.context.analysis:
            raise ExecutionError(step.name, "No analysis result available", recoverable=False)

        generator = DockerfileGenerator()
        self.context.dockerfile_content = generator.generate(self.context.analysis)

        if self.context.repo_path and not self.dry_run:
            dockerfile_path = Path(self.context.repo_path) / "Dockerfile"
            dockerfile_path.write_text(self.context.dockerfile_content)

        self.context.artifacts["dockerfile"] = self.context.dockerfile_content

    def _handle_validate_dockerfile(self, step: PlanStep, intent: dict):
        if not self.context.repo_path:
            return
        dockerfile = Path(self.context.repo_path) / "Dockerfile"
        if not dockerfile.exists():
            step.status = StepStatus.SKIPPED
            return
        self.context.dockerfile_content = dockerfile.read_text()

    def _handle_build_image(self, step: PlanStep, intent: dict):
        if not self.context.repo_path:
            raise ExecutionError(step.name, "No repository path set", recoverable=False)

        repo_name = intent.get("source_repo", "app").split("/")[-1].replace(".git", "")
        env = intent.get("environment", "latest")
        self.context.image_name = repo_name
        self.context.image_tag = env

        try:
            self._run_cmd(
                ["docker", "build", "-t", f"{repo_name}:{env}", "."],
                cwd=self.context.repo_path,
            )
        except subprocess.CalledProcessError as e:
            raise ExecutionError(step.name, f"Docker build failed: {e.stderr}")
        except FileNotFoundError:
            raise ExecutionError(step.name, "Docker is not installed", recoverable=False)

    def _handle_push_image(self, step: PlanStep, intent: dict):
        if not self.context.full_image_ref:
            raise ExecutionError(step.name, "No image to push", recoverable=False)

        if self.dry_run:
            return

        try:
            self._run_cmd(["docker", "push", self.context.full_image_ref])
        except subprocess.CalledProcessError as e:
            raise ExecutionError(step.name, f"Push failed: {e.stderr}")

    def _handle_deploy_ecs_configure(self, step: PlanStep, intent: dict):
        if self.dry_run:
            return
        # Generate ECS task definition JSON
        self.context.artifacts["ecs_task_def"] = {
            "family": self.context.image_name or "app",
            "containerDefinitions": [{
                "name": self.context.image_name or "app",
                "image": self.context.full_image_ref,
                "portMappings": [{"containerPort": self.context.analysis.port or 8080}] if self.context.analysis else [],
                "essential": True,
                "memory": 512,
                "cpu": 256,
            }],
        }

    def _handle_deploy_ecs(self, step: PlanStep, intent: dict):
        if self.dry_run:
            return
        env = step.context.get("environment", "staging")
        cluster = f"forge-{env}"
        service = self.context.image_name or "app"

        try:
            self._run_cmd([
                "aws", "ecs", "update-service",
                "--cluster", cluster,
                "--service", service,
                "--force-new-deployment",
            ])
        except subprocess.CalledProcessError as e:
            raise ExecutionError(step.name, f"ECS deployment failed: {e.stderr}")
        except FileNotFoundError:
            raise ExecutionError(step.name, "AWS CLI is not installed", recoverable=False)

    def _handle_deploy_cloud_run(self, step: PlanStep, intent: dict):
        if self.dry_run:
            return
        service = self.context.image_name or "app"
        image = self.context.full_image_ref
        if not image:
            raise ExecutionError(step.name, "No image available for deployment", recoverable=False)

        try:
            self._run_cmd([
                "gcloud", "run", "deploy", service,
                "--image", image,
                "--platform", "managed",
                "--allow-unauthenticated",
            ])
        except subprocess.CalledProcessError as e:
            raise ExecutionError(step.name, f"Cloud Run deploy failed: {e.stderr}")

    def _handle_deploy_lambda_package(self, step: PlanStep, intent: dict):
        if self.dry_run:
            return
        self.context.artifacts["lambda_package"] = "function.zip"

    def _handle_deploy_lambda(self, step: PlanStep, intent: dict):
        if self.dry_run:
            return
        func_name = self.context.image_name or "app"
        try:
            self._run_cmd([
                "aws", "lambda", "update-function-code",
                "--function-name", func_name,
                "--zip-file", "fileb://function.zip",
            ])
        except subprocess.CalledProcessError as e:
            raise ExecutionError(step.name, f"Lambda deploy failed: {e.stderr}")

    def _handle_deploy_k8s_generate(self, step: PlanStep, intent: dict):
        if not self.context.analysis:
            return
        port = self.context.analysis.port or 8080
        name = self.context.image_name or "app"
        image = self.context.full_image_ref or f"{name}:latest"

        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
      - name: {name}
        image: {image}
        ports:
        - containerPort: {port}
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: {name}
spec:
  selector:
    app: {name}
  ports:
  - port: 80
    targetPort: {port}
  type: LoadBalancer
"""
        self.context.artifacts["k8s_manifest"] = manifest
        if self.context.repo_path and not self.dry_run:
            manifest_path = Path(self.context.repo_path) / "k8s.yaml"
            manifest_path.write_text(manifest)

    def _handle_deploy_k8s_apply(self, step: PlanStep, intent: dict):
        if self.dry_run:
            return
        manifest = self.context.artifacts.get("k8s_manifest")
        if not manifest or not self.context.repo_path:
            raise ExecutionError(step.name, "No Kubernetes manifest generated")

        manifest_path = Path(self.context.repo_path) / "k8s.yaml"
        try:
            self._run_cmd(["kubectl", "apply", "-f", str(manifest_path)])
        except subprocess.CalledProcessError as e:
            raise ExecutionError(step.name, f"kubectl apply failed: {e.stderr}")

    def _handle_deploy_azure(self, step: PlanStep, intent: dict):
        if self.dry_run:
            return
        name = self.context.image_name or "app"
        image = self.context.full_image_ref
        if not image:
            raise ExecutionError(step.name, "No image available")

        try:
            self._run_cmd([
                "az", "containerapp", "update",
                "--name", name,
                "--image", image,
            ])
        except subprocess.CalledProcessError as e:
            raise ExecutionError(step.name, f"Azure deploy failed: {e.stderr}")

    def _handle_deploy_generic(self, step: PlanStep, intent: dict):
        pass

    def _handle_health_check(self, step: PlanStep, intent: dict):
        if self.dry_run:
            return
        url = self.context.deployed_url
        if not url:
            return

        import urllib.request
        for attempt in range(3):
            try:
                resp = urllib.request.urlopen(url, timeout=10)
                if resp.status < 400:
                    return
            except Exception:
                if attempt < 2:
                    time.sleep(5)
        raise ExecutionError(step.name, f"Health check failed for {url}")

    def _handle_cleanup(self, step: PlanStep, intent: dict):
        if self.context.repo_path and os.path.exists(self.context.repo_path):
            shutil.rmtree(self.context.repo_path, ignore_errors=True)
            self.context.repo_path = None
