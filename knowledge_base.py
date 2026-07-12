class KnowledgeBase:
    """
    Stores and retrieves information about cloud services, best practices, and past deployments.
    """
    def __init__(self):
        print("🧠 Knowledge Base initialized.")

    def get_best_practices(self, target_platform: str) -> list[str]:
        """Retrieves best practices for a given cloud platform."""
        print(f"📚 Retrieving best practices for {target_platform}...")
        # In a real implementation, this would query a database or a file-based knowledge store.
        return [
            "Use multi-stage builds for smaller Docker images.",
            "Scan images for vulnerabilities.",
            "Implement logging and monitoring.",
        ]
