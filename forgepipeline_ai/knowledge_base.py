"""
Knowledge base with real deployment patterns, best practices,
and framework-specific guidance for containerization and cloud deployment.
"""

from dataclasses import dataclass


@dataclass
class DeploymentPattern:
    name: str
    description: str
    when_to_use: str
    steps: list[str]


BEST_PRACTICES: dict[str, list[str]] = {
    "docker": [
        "Use multi-stage builds to minimize final image size",
        "Run as non-root user for security",
        "Use .dockerignore to exclude unnecessary files",
        "Pin base image versions for reproducibility",
        "Order Dockerfile instructions from least to most frequently changed for layer caching",
        "Use COPY instead of ADD unless extracting archives",
        "Combine RUN commands with && to reduce layers",
        "Scan images with trivy or snyk before deploying",
    ],
    "aws-ecs": [
        "Use Fargate for serverless containers (no EC2 management)",
        "Set memory and CPU limits in task definitions",
        "Use Application Load Balancer for HTTP traffic",
        "Enable container insights for monitoring",
        "Store secrets in AWS Secrets Manager, not env vars",
        "Use ECR for private container registry",
        "Configure health checks with appropriate grace periods",
        "Use service auto-scaling based on CPU/memory metrics",
    ],
    "aws-lambda": [
        "Keep deployment packages small (<50MB unzipped)",
        "Use Lambda layers for shared dependencies",
        "Set appropriate memory (also controls CPU allocation)",
        "Configure reserved concurrency for critical functions",
        "Use environment variables for configuration",
        "Implement structured logging with CloudWatch",
        "Set appropriate timeout (max 15 minutes)",
    ],
    "gcp-run": [
        "Use concurrency settings to handle multiple requests per container",
        "Set minimum instances to avoid cold starts in production",
        "Use Cloud Build for CI/CD integration",
        "Configure memory limits based on application needs",
        "Use Secret Manager for sensitive configuration",
        "Enable CPU boost for faster cold starts",
        "Use service revisions for safe rollbacks",
    ],
    "kubernetes": [
        "Always set resource requests and limits",
        "Use readiness and liveness probes",
        "Store configuration in ConfigMaps and secrets",
        "Use namespaces to isolate environments",
        "Implement horizontal pod autoscaling",
        "Use rolling update strategy for zero-downtime deploys",
        "Set pod disruption budgets for high availability",
        "Use network policies for pod-to-pod security",
    ],
    "azure": [
        "Use Container Apps for serverless container workloads",
        "Configure revision-based traffic splitting for canary deployments",
        "Use managed identity for secure service-to-service auth",
        "Enable Dapr sidecar for microservice patterns",
        "Store secrets in Azure Key Vault",
        "Configure scaling rules based on HTTP traffic or queue length",
    ],
    "general": [
        "Use environment variables for configuration (12-factor app)",
        "Implement graceful shutdown handling (SIGTERM)",
        "Add health check endpoints (/health or /healthz)",
        "Use structured JSON logging",
        "Externalize state (databases, caches, object storage)",
        "Implement retry logic with exponential backoff for external calls",
        "Use connection pooling for database connections",
    ],
}

FRAMEWORK_PATTERNS: dict[str, dict[str, str]] = {
    "fastapi": {
        "dockerfile_notes": "Use uvicorn with multiple workers in production",
        "health_endpoint": "Add a /health GET endpoint returning 200",
        "production_server": "uvicorn app.main:app --host 0.0.0.0 --workers 4",
        "common_issues": "Ensure async dependencies don't block the event loop",
    },
    "django": {
        "dockerfile_notes": "Run collectstatic in build stage, use gunicorn in production",
        "health_endpoint": "Add django-health-check or a simple view",
        "production_server": "gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 4",
        "common_issues": "Set ALLOWED_HOSTS, configure static file serving (whitenoise or nginx)",
    },
    "flask": {
        "dockerfile_notes": "Never use flask run in production, use gunicorn",
        "health_endpoint": "Add a /health route",
        "production_server": "gunicorn -w 4 -b 0.0.0.0:5000 app:app",
        "common_issues": "Set SECRET_KEY from env, disable debug mode",
    },
    "nextjs": {
        "dockerfile_notes": "Use standalone output mode for minimal image size",
        "health_endpoint": "Add pages/api/health.ts",
        "production_server": "node server.js (standalone) or next start",
        "common_issues": "Set NEXT_PUBLIC_ env vars at build time, not runtime",
    },
    "express": {
        "dockerfile_notes": "Use node directly, not npm start, for proper signal handling",
        "health_endpoint": "Add GET /health endpoint",
        "production_server": "node index.js",
        "common_issues": "Handle uncaught exceptions, set trust proxy behind LB",
    },
    "react-vite": {
        "dockerfile_notes": "Build static files then serve with nginx",
        "health_endpoint": "Not applicable (static site)",
        "production_server": "nginx",
        "common_issues": "Configure SPA fallback in nginx, set API proxy for CORS",
    },
    "spring-boot": {
        "dockerfile_notes": "Use layered JAR extraction for optimal Docker layer caching",
        "health_endpoint": "Enable Spring Boot Actuator /actuator/health",
        "production_server": "java -jar app.jar",
        "common_issues": "Set JVM heap limits to match container memory, use -XX:MaxRAMPercentage",
    },
}

DEPLOYMENT_PATTERNS: list[DeploymentPattern] = [
    DeploymentPattern(
        name="Blue-Green",
        description="Run two identical environments, switch traffic atomically",
        when_to_use="Zero-downtime deploys with instant rollback needed",
        steps=["Deploy to inactive environment", "Run smoke tests", "Switch traffic", "Keep old env as rollback"],
    ),
    DeploymentPattern(
        name="Canary",
        description="Route a small percentage of traffic to new version",
        when_to_use="Gradual rollout with risk mitigation",
        steps=[
            "Deploy new version alongside old",
            "Route 5% traffic",
            "Monitor metrics",
            "Gradually increase or rollback",
        ],
    ),
    DeploymentPattern(
        name="Rolling Update",
        description="Replace instances one at a time",
        when_to_use="Standard deployments where brief mixed versions are acceptable",
        steps=["Update one instance", "Health check", "Continue to next", "Complete when all updated"],
    ),
]


class KnowledgeBase:
    """Provides deployment patterns, best practices, and framework-specific guidance."""

    def get_best_practices(self, target_platform: str) -> list[str]:
        practices = BEST_PRACTICES.get("general", [])

        # Add platform-specific practices
        for key in BEST_PRACTICES:
            if key in target_platform:
                practices = BEST_PRACTICES[key] + practices
                break

        # Always include Docker best practices for containerized deployments
        if target_platform not in ("aws-lambda",):
            practices = BEST_PRACTICES["docker"][:4] + practices

        return practices

    def get_framework_guidance(self, framework: str | None) -> dict[str, str] | None:
        if not framework:
            return None
        return FRAMEWORK_PATTERNS.get(framework)

    def get_deployment_patterns(self) -> list[DeploymentPattern]:
        return DEPLOYMENT_PATTERNS

    def recommend_pattern(self, environment: str) -> DeploymentPattern:
        if environment == "production":
            return DEPLOYMENT_PATTERNS[1]  # Canary
        return DEPLOYMENT_PATTERNS[2]  # Rolling Update
