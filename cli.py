import typer
from typing_extensions import Annotated

from intent_parser import IntentParser
from planning_agent import PlanningAgent
from execution_engine import ExecutionEngine
from knowledge_base import KnowledgeBase

app = typer.Typer(help="ForgePipeline AI: An agentic cloud deployment tool.")


@app.command()
def deploy(
    repo: Annotated[str, typer.Option(help="URL of the source code repository.")],
    target: Annotated[str, typer.Option(help="Cloud target for deployment (e.g., aws-ecs, gcp-run).")],
    env: Annotated[str, typer.Option(help="Deployment environment (e.g., staging, production).")]
):
    """
    Analyze a repository and deploy it to a specified cloud target.
    """
    print(f"🚀 Initializing deployment for repo: {repo}")
    print(f"☁️ Target: {target} | Environment: {env}")

    # 1. Parse Intent
    parser = IntentParser()
    intent = parser.parse(repo=repo, target=target, env=env)

    # 2. Create Plan
    planner = PlanningAgent()
    plan = planner.create_plan(intent)

    # 3. Execute Plan
    engine = ExecutionEngine()
    engine.execute_plan(plan)

    # 4. Show Best Practices
    kb = KnowledgeBase()
    best_practices = kb.get_best_practices(target_platform=target)
    print("\n💡 Best Practices:")
    for practice in best_practices:
        print(f"   - {practice}")

    print("\n✅ Deployment workflow complete.")


if __name__ == "__main__":
    app()