"""
Intent parser that converts CLI arguments, natural language commands,
or structured input into a normalized intent dictionary.
"""

import re
from dataclasses import dataclass, field


@dataclass
class DeploymentIntent:
    action: str = "deploy"
    source_repo: str | None = None
    target_platform: str | None = None
    environment: str = "staging"
    no_docker: bool = False
    registry_url: str | None = None
    region: str | None = None
    options: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != {} and v is not False}


# Patterns for natural language parsing
TARGET_ALIASES: dict[str, str] = {
    "ecs": "aws-ecs",
    "fargate": "aws-ecs",
    "aws": "aws-ecs",
    "lambda": "aws-lambda",
    "cloud run": "gcp-run",
    "cloudrun": "gcp-run",
    "gcp": "gcp-run",
    "google cloud": "gcp-run",
    "azure": "azure-container-apps",
    "container apps": "azure-container-apps",
    "k8s": "kubernetes",
    "kube": "kubernetes",
}

ENV_ALIASES: dict[str, str] = {
    "prod": "production",
    "stg": "staging",
    "dev": "development",
    "stage": "staging",
}


class IntentParser:
    """Parses structured CLI input or natural language into a DeploymentIntent."""

    def parse(self, repo: str | None = None, target: str | None = None, env: str | None = None,
              natural_language: str | None = None, **kwargs) -> dict:
        if natural_language:
            return self._parse_natural(natural_language, **kwargs)
        return self._parse_structured(repo, target, env, **kwargs)

    def _parse_structured(self, repo: str | None, target: str | None, env: str | None, **kwargs) -> dict:
        intent = DeploymentIntent()
        intent.source_repo = repo
        intent.target_platform = self._normalize_target(target) if target else None
        intent.environment = self._normalize_env(env) if env else "staging"
        intent.no_docker = kwargs.get("no_docker", False)
        intent.registry_url = kwargs.get("registry")
        intent.region = kwargs.get("region")
        return intent.to_dict()

    def _parse_natural(self, text: str, **kwargs) -> dict:
        intent = DeploymentIntent()
        text_lower = text.lower()

        # Detect action
        if any(w in text_lower for w in ["rollback", "revert", "undo"]):
            intent.action = "rollback"
        elif any(w in text_lower for w in ["status", "check", "health"]):
            intent.action = "status"
        elif any(w in text_lower for w in ["destroy", "teardown", "delete"]):
            intent.action = "destroy"
        else:
            intent.action = "deploy"

        # Extract repo URL
        url_match = re.search(r'(https?://\S+|git@\S+)', text)
        if url_match:
            intent.source_repo = url_match.group(1)

        # Extract target platform
        for alias, platform in sorted(TARGET_ALIASES.items(), key=lambda x: -len(x[0])):
            if alias in text_lower:
                intent.target_platform = platform
                break

        # Extract environment
        for alias, env_name in ENV_ALIASES.items():
            if alias in text_lower:
                intent.environment = env_name
                break
        if "production" in text_lower:
            intent.environment = "production"
        elif "staging" in text_lower:
            intent.environment = "staging"

        # Extract region
        region_match = re.search(r'(us-east-\d|us-west-\d|eu-west-\d|eu-central-\d|ap-southeast-\d)', text_lower)
        if region_match:
            intent.region = region_match.group(1)

        return intent.to_dict()

    def _normalize_target(self, target: str) -> str:
        return TARGET_ALIASES.get(target.lower(), target.lower())

    def _normalize_env(self, env: str) -> str:
        return ENV_ALIASES.get(env.lower(), env.lower())
