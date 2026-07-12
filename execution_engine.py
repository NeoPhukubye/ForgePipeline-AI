import subprocess
import tempfile
import shutil
import os

class ExecutionEngine:
    """
    Carries out the steps planned by the agent.
    """
    def __init__(self):
        self.repo_path = None
        self.image_name = None

    def execute_plan(self, plan: list[dict], intent: dict):
        """Iterates through a plan and executes each step."""
        print("⚙️ Execution engine starting...")
        for step in plan:
            step_name = step["step"]
            handler = getattr(self, f"_handle_{step_name}", self._handle_unknown)
            handler(step, intent)

    def _handle_unknown(self, step: dict, intent: dict):
        print(f"   -> Unknown step: {step['step']}")

    def _handle_clone_repo(self, step: dict, intent: dict):
        print(f"   -> Executing step: {step['step']}")
        repo_url = intent.get("source_repo")
        if not repo_url:
            print("      -> Error: source_repo not found in intent.")
            return

        self.repo_path = tempfile.mkdtemp()
        print(f"      -> Cloning {repo_url} into {self.repo_path}")
        try:
            subprocess.run(["git", "clone", repo_url, self.repo_path], check=True)
            print("      -> Cloning complete.")
        except subprocess.CalledProcessError as e:
            print(f"      -> Error cloning repository: {e}")
            self.repo_path = None
        except Exception as e:
            print(f"      -> An unexpected error occurred: {e}")
            self.repo_path = None

    def _handle_analyze_code(self, step: dict, intent: dict):
        print(f"   -> Executing step: {step['step']}")
        if not self.repo_path:
            print("      -> Error: repo_path not set. Did clone_repo fail?")
            return

        print(f"      -> Analyzing code in {self.repo_path}")
        file_counts = {}
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                ext = file.split('.')[-1]
                if ext:
                    file_counts[ext] = file_counts.get(ext, 0) + 1

        if not file_counts:
            print("      -> No files found to analyze.")
            return

        print("      -> File type summary:")
        for ext, count in sorted(file_counts.items(), key=lambda item: item[1], reverse=True)[:5]:
            print(f"         - .{ext}: {count} files")


    def _handle_generate_dockerfile(self, step: dict, intent: dict):
        print(f"   -> Executing step: {step['step']}")
        if not self.repo_path:
            print("      -> Error: repo_path not set. Did clone_repo fail?")
            return

        dockerfile_path = os.path.join(self.repo_path, "Dockerfile")
        print(f"      -> Generating Dockerfile at {dockerfile_path}")

        try:
            with open(dockerfile_path, "w") as f:
                f.write("# This is a placeholder Dockerfile\n")
                f.write("FROM scratch\n")
            print("      -> Dockerfile generated.")
        except IOError as e:
            print(f"      -> Error generating Dockerfile: {e}")

    def _handle_build_image(self, step: dict, intent: dict):
        print(f"   -> Executing step: {step['step']}")
        if not self.repo_path:
            print("      -> Error: repo_path not set. Did clone_repo/generate_dockerfile fail?")
            return

        repo_name = intent.get("source_repo").split('/')[-1].replace('.git', '')
        env = intent.get("environment")
        self.image_name = f"{repo_name}:{env}"

        print(f"      -> Building Docker image: {self.image_name}")
        try:
            subprocess.run(
                ["docker", "build", "-t", self.image_name, "."],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            print("      -> Docker image built successfully.")
        except subprocess.CalledProcessError as e:
            print(f"      -> Error building Docker image: {e.stderr}")
            self.image_name = None
        except FileNotFoundError:
            print("      -> Error: docker command not found. Is Docker installed and in your PATH?")
            self.image_name = None
        except Exception as e:
            print(f"      -> An unexpected error occurred: {e}")
            self.image_name = None

    def _handle_push_image(self, step: dict, intent: dict):
        print(f"   -> Executing step: {step['step']}")

    def _handle_deploy(self, step: dict, intent: dict):
        print(f"   -> Executing step: {step['step']}")

    def _handle_cleanup(self, step: dict, intent: dict):
        print(f"   -> Executing step: {step['step']}")
        if self.repo_path:
            print(f"      -> Cleaning up temporary directory: {self.repo_path}")
            shutil.rmtree(self.repo_path)
            self.repo_path = None