class PlanningAgent:
    """
    Breaks down a high-level goal into a sequence of executable steps.
    """
    def create_plan(self, intent: dict) -> list[dict]:
        """Analyzes user intent and generates a step-by-step deployment plan."""
        print(f"🤖 Planning agent received intent: {intent}")
        # In a real implementation, this would involve LLM calls or rule-based logic.
        return [{"step": "clone_repo"}, {"step": "analyze_code"}, {"step": "deploy"}]