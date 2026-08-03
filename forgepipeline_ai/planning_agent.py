"""
Planning agent that creates dynamic, context-aware deployment plans
based on code analysis results and deployment targets.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .analyzer import AnalysisResult


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    name: str
    description: str
    handler: str
    status: StepStatus = StepStatus.PENDING
    required: bool = True
    skip_condition: str | None = None
    retry_count: int = 0
    max_retries: int = 2
    context: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "handler": self.handler,
            "status": self.status.value,
            "required": self.required,
            "context": self.context,
        }


@dataclass
class DeploymentPlan:
    steps: list[PlanStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        return self.completed_steps / self.total_steps

    def summary(self) -> str:
        lines = [f"Deployment Plan ({self.total_steps} steps):"]
        for i, step in enumerate(self.steps, 1):
            icon = {"pending": "○", "running": "◉", "completed": "●", "failed": "✗", "skipped": "◌"}
            lines.append(f"  {icon[step.status.value]} {i}. {step.description}")
        return "\n".join(lines)


class PlanningAgent:
    """Creates dynamic deployment plans based on analysis results and intent."""

    def create_plan(self, intent: dict, analysis: AnalysisResult | None = None) -> DeploymentPlan:
        plan = DeploymentPlan()
        plan.metadata = {
            "target": intent.get("target_platform"),
            "environment": intent.get("environment"),
            "language": analysis.language if analysis else "unknown",
            "framework": analysis.framework if analysis else None,
        }

        # Always start with repo acquisition
        plan.steps.append(PlanStep(
            name="clone_repo",
            description=f"Clone repository from {intent.get('source_repo', 'source')}",
            handler="clone_repo",
            context={"repo_url": intent.get("source_repo")},
        ))

        # Code analysis
        plan.steps.append(PlanStep(
            name="analyze_code",
            description="Analyze codebase to detect language, framework, and dependencies",
            handler="analyze_code",
            depends_on=["clone_repo"],
        ))

        # Dockerfile generation (unless one exists or docker is skipped)
        if not intent.get("no_docker"):
            if analysis and analysis.has_dockerfile:
                plan.steps.append(PlanStep(
                    name="validate_dockerfile",
                    description="Validate existing Dockerfile against best practices",
                    handler="validate_dockerfile",
                    depends_on=["analyze_code"],
                    required=False,
                ))
            else:
                plan.steps.append(PlanStep(
                    name="generate_dockerfile",
                    description="Generate optimized Dockerfile based on analysis",
                    handler="generate_dockerfile",
                    depends_on=["analyze_code"],
                ))

            # Build image
            plan.steps.append(PlanStep(
                name="build_image",
                description="Build Docker image",
                handler="build_image",
                depends_on=["generate_dockerfile"] if not (analysis and analysis.has_dockerfile) else ["validate_dockerfile"],
                max_retries=1,
            ))

            # Push image to registry
            plan.steps.append(PlanStep(
                name="push_image",
                description="Push image to container registry",
                handler="push_image",
                depends_on=["build_image"],
            ))

        # Deploy based on target platform
        target = intent.get("target_platform", "")
        deploy_steps = self._get_deploy_steps(target, intent)
        for step in deploy_steps:
            step.depends_on = ["push_image"] if not intent.get("no_docker") else ["analyze_code"]
            plan.steps.append(step)

        # Health check
        plan.steps.append(PlanStep(
            name="health_check",
            description="Verify deployment health and connectivity",
            handler="health_check",
            depends_on=[deploy_steps[-1].name] if deploy_steps else ["analyze_code"],
            required=False,
        ))

        # Cleanup
        plan.steps.append(PlanStep(
            name="cleanup",
            description="Clean up temporary files and resources",
            handler="cleanup",
            depends_on=["health_check"],
            required=False,
        ))

        return plan

    def _get_deploy_steps(self, target: str, intent: dict) -> list[PlanStep]:
        env = intent.get("environment", "staging")

        if "ecs" in target:
            return [
                PlanStep(
                    name="configure_ecs",
                    description=f"Configure ECS task definition for {env}",
                    handler="deploy_ecs_configure",
                    context={"environment": env},
                ),
                PlanStep(
                    name="deploy_ecs",
                    description=f"Deploy to ECS ({env})",
                    handler="deploy_ecs",
                    depends_on=["configure_ecs"],
                    context={"environment": env},
                ),
            ]
        elif "lambda" in target:
            return [
                PlanStep(
                    name="package_lambda",
                    description="Package application for Lambda deployment",
                    handler="deploy_lambda_package",
                    context={"environment": env},
                ),
                PlanStep(
                    name="deploy_lambda",
                    description=f"Deploy Lambda function ({env})",
                    handler="deploy_lambda",
                    depends_on=["package_lambda"],
                    context={"environment": env},
                ),
            ]
        elif "gcp-run" in target or "cloud-run" in target:
            return [
                PlanStep(
                    name="deploy_cloud_run",
                    description=f"Deploy to Google Cloud Run ({env})",
                    handler="deploy_cloud_run",
                    context={"environment": env},
                ),
            ]
        elif "azure" in target:
            return [
                PlanStep(
                    name="deploy_azure",
                    description=f"Deploy to Azure Container Apps ({env})",
                    handler="deploy_azure_container_apps",
                    context={"environment": env},
                ),
            ]
        elif "k8s" in target or "kubernetes" in target:
            return [
                PlanStep(
                    name="generate_manifests",
                    description="Generate Kubernetes manifests",
                    handler="deploy_k8s_generate",
                    context={"environment": env},
                ),
                PlanStep(
                    name="deploy_k8s",
                    description=f"Apply Kubernetes manifests ({env})",
                    handler="deploy_k8s_apply",
                    depends_on=["generate_manifests"],
                    context={"environment": env},
                ),
            ]
        else:
            return [
                PlanStep(
                    name="deploy_generic",
                    description=f"Deploy to {target} ({env})",
                    handler="deploy_generic",
                    context={"target": target, "environment": env},
                ),
            ]
