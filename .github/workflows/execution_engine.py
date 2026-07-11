class ExecutionEngine:
    """
    Carries out the steps planned by the agent.
    """
    def execute_plan(self, plan: list[dict]):
        """Iterates through a plan and executes each step."""
        print("⚙️ Execution engine starting...")
        for step in plan:
            print(f"   -> Executing step: {step['step']}")