"""
CLI interface for ForgePipeline AI with rich output, progress tracking,
and interactive confirmation for production deployments.
"""

from typing import Optional

import typer
from typing_extensions import Annotated

from .analyzer import CodeAnalyzer
from .dockerfile_generator import DockerfileGenerator
from .execution_engine import ExecutionEngine
from .intent_parser import IntentParser
from .knowledge_base import KnowledgeBase
from .planning_agent import DeploymentPlan, PlanningAgent, PlanStep, StepStatus

app = typer.Typer(
    help="ForgePipeline AI: Agentic cloud deployment from intent to production.",
    no_args_is_help=True,
)


def _step_icon(status: StepStatus) -> str:
    return {"pending": "○", "running": "◉", "completed": "✓", "failed": "✗", "skipped": "◌"}[status.value]


def _print_header(text: str):
    width = 60
    typer.echo(f"\n{'━' * width}")
    typer.echo(f"  {text}")
    typer.echo(f"{'━' * width}")


def _print_plan(plan: DeploymentPlan):
    typer.echo("\n  Plan:")
    for i, step in enumerate(plan.steps, 1):
        icon = _step_icon(step.status)
        typer.echo(f"    {icon} {i}. {step.description}")
    typer.echo("")


def _print_analysis(analysis):
    typer.echo("\n  Analysis Results:")
    typer.echo(f"    Language:        {analysis.language}")
    if analysis.framework:
        typer.echo(f"    Framework:       {analysis.framework}")
    if analysis.package_manager:
        typer.echo(f"    Package Manager: {analysis.package_manager}")
    if analysis.port:
        typer.echo(f"    Port:            {analysis.port}")
    if analysis.entry_point:
        typer.echo(f"    Entry Point:     {analysis.entry_point}")
    if analysis.start_command:
        typer.echo(f"    Start Command:   {analysis.start_command}")
    typer.echo("")


def _on_step_start(step: PlanStep):
    typer.echo(f"  ◉ {step.description}...")


def _on_step_complete(step: PlanStep):
    typer.echo(f"  ✓ {step.description} [done]")


def _on_step_fail(step: PlanStep, error: Exception):
    typer.echo(f"  ✗ {step.description} [FAILED]")
    typer.echo(f"    Error: {error}")


@app.command()
def deploy(
    repo: Annotated[str, typer.Option("--repo", "-r", help="Repository URL or local path.")],
    target: Annotated[str, typer.Option("--target", "-t", help="Cloud target (aws-ecs, gcp-run, kubernetes, azure, aws-lambda).")],
    env: Annotated[str, typer.Option("--env", "-e", help="Environment (staging, production, development).")] = "staging",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Simulate without executing.")] = False,
    no_docker: Annotated[bool, typer.Option("--no-docker", help="Skip Docker build/push steps.")] = False,
    registry: Annotated[Optional[str], typer.Option("--registry", help="Container registry URL.")] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed output.")] = False,
):
    """Deploy a repository to a cloud target."""
    _print_header("ForgePipeline AI")
    typer.echo(f"  Repository: {repo}")
    typer.echo(f"  Target:     {target}")
    typer.echo(f"  Environment:{env}")
    if dry_run:
        typer.echo("  Mode:       DRY RUN")

    # Parse intent
    parser = IntentParser()
    intent = parser.parse(repo=repo, target=target, env=env, no_docker=no_docker, registry=registry)

    # Create plan
    planner = PlanningAgent()
    plan = planner.create_plan(intent)
    _print_plan(plan)

    # Confirm production deployments
    if env in ("production", "prod") and not yes and not dry_run:
        confirmed = typer.confirm("  Deploy to PRODUCTION?", default=False)
        if not confirmed:
            typer.echo("  Aborted.")
            raise typer.Exit(code=0)

    # Execute
    engine = ExecutionEngine(dry_run=dry_run, verbose=verbose)
    engine.on_step_start(_on_step_start)
    engine.on_step_complete(_on_step_complete)
    engine.on_step_fail(_on_step_fail)

    _print_header("Executing")
    ctx = engine.execute_plan(plan, intent)

    # Print analysis if available
    if ctx.analysis:
        _print_analysis(ctx.analysis)

    # Summary
    _print_header("Summary")
    completed = sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED)
    failed = sum(1 for s in plan.steps if s.status == StepStatus.FAILED)
    skipped = sum(1 for s in plan.steps if s.status == StepStatus.SKIPPED)

    typer.echo(f"  Completed: {completed}/{plan.total_steps}")
    if skipped:
        typer.echo(f"  Skipped:   {skipped}")
    if failed:
        typer.echo(f"  Failed:    {failed}")
        for err in ctx.errors:
            typer.echo(f"    - {err}")
        raise typer.Exit(code=1)

    # Best practices
    kb = KnowledgeBase()
    practices = kb.get_best_practices(target)
    if practices:
        typer.echo("\n  Recommendations:")
        for p in practices[:5]:
            typer.echo(f"    • {p}")

    if ctx.analysis and ctx.analysis.framework:
        guidance = kb.get_framework_guidance(ctx.analysis.framework)
        if guidance:
            typer.echo(f"\n  Framework tips ({ctx.analysis.framework}):")
            for key, val in list(guidance.items())[:3]:
                typer.echo(f"    {key}: {val}")

    typer.echo(f"\n  {'[DRY RUN] ' if dry_run else ''}Deployment complete.\n")


@app.command()
def analyze(
    path: Annotated[str, typer.Argument(help="Path to repository or project directory.")] = ".",
):
    """Analyze a codebase and show detected configuration."""
    _print_header("Code Analysis")
    analyzer = CodeAnalyzer()
    try:
        result = analyzer.analyze(path)
    except ValueError as e:
        typer.echo(f"  Error: {e}")
        raise typer.Exit(code=1)

    _print_analysis(result)

    if result.dependencies:
        typer.echo(f"  Dependencies ({len(result.dependencies)}):")
        for dep in result.dependencies[:15]:
            typer.echo(f"    - {dep}")
        if len(result.dependencies) > 15:
            typer.echo(f"    ... and {len(result.dependencies) - 15} more")
    typer.echo("")


@app.command()
def generate(
    path: Annotated[str, typer.Argument(help="Path to repository or project directory.")] = ".",
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Write Dockerfile to path (default: stdout).")] = None,
):
    """Generate a Dockerfile for the given project."""
    analyzer = CodeAnalyzer()
    try:
        result = analyzer.analyze(path)
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

    generator = DockerfileGenerator()
    dockerfile = generator.generate(result)

    if output:
        with open(output, "w") as f:
            f.write(dockerfile)
        typer.echo(f"Dockerfile written to {output}")
    else:
        typer.echo(dockerfile)


@app.command()
def plan(
    repo: Annotated[str, typer.Option("--repo", "-r", help="Repository URL.")],
    target: Annotated[str, typer.Option("--target", "-t", help="Cloud target.")],
    env: Annotated[str, typer.Option("--env", "-e", help="Environment.")] = "staging",
):
    """Show the deployment plan without executing it."""
    parser = IntentParser()
    intent = parser.parse(repo=repo, target=target, env=env)

    planner = PlanningAgent()
    deployment_plan = planner.create_plan(intent)

    _print_header("Deployment Plan")
    _print_plan(deployment_plan)

    kb = KnowledgeBase()
    pattern = kb.recommend_pattern(env)
    typer.echo(f"  Recommended strategy: {pattern.name}")
    typer.echo(f"  {pattern.description}\n")


if __name__ == "__main__":
    app()
