class ExecutionEngine:
    """
    Carries out the steps planned by the agent.
    """
    def execute_plan(self, plan: list[dict]):
        """Iterates through a plan and executes each step."""
        print("⚙️ Execution engine starting...")
        for step in plan:
            step_name = step["step"]
            handler = getattr(self, f"_handle_{step_name}", self._handle_unknown)
            handler(step)

    def _handle_unknown(self, step: dict):
        print(f"   -> Unknown step: {step['step']}")

    def _handle_clone_repo(self, step: dict):
        print(f"   -> Executing step: {step['step']}")

    def _handle_analyze_code(self, step: dict):
        print(f"   -> Executing step: {step['step']}")

    def _handle_generate_dockerfile(self, step: dict):
        print(f"   -> Executing step: {step['step']}")

    def _handle_build_image(self, step: dict):
        print(f"   -> Executing step: {step['step']}")

    def _handle_push_image(self, step: dict):
        print(f"   -> Executing step: {step['step']}")

    def _handle_deploy(self, step: dict):
        print(f"   -> Executing step: {step['step']}")