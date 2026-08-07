"""
Code analyzer that inspects a repository to determine language, framework,
dependencies, entry points, exposed ports, and build configuration.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AnalysisResult:
    language: str = "unknown"
    framework: str | None = None
    package_manager: str | None = None
    entry_point: str | None = None
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)
    port: int | None = None
    python_version: str | None = None
    node_version: str | None = None
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    build_command: str | None = None
    start_command: str | None = None
    static_output_dir: str | None = None
    env_vars: list[str] = field(default_factory=list)
    multi_service: bool = False
    services: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != [] and v != "unknown"}


class CodeAnalyzer:
    """Inspects a repository directory and produces an AnalysisResult."""

    def analyze(self, repo_path: str) -> AnalysisResult:
        path = Path(repo_path)
        if not path.is_dir():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        result = AnalysisResult()
        result.has_dockerfile = (path / "Dockerfile").exists()
        result.has_docker_compose = (path / "docker-compose.yml").exists() or (path / "compose.yml").exists()

        # Detect language and framework
        if (path / "package.json").exists():
            self._analyze_node(path, result)
        elif (path / "requirements.txt").exists() or (path / "pyproject.toml").exists() or (path / "Pipfile").exists():
            self._analyze_python(path, result)
        elif (path / "go.mod").exists():
            self._analyze_go(path, result)
        elif (path / "Cargo.toml").exists():
            self._analyze_rust(path, result)
        elif (path / "pom.xml").exists() or (path / "build.gradle").exists():
            self._analyze_java(path, result)
        else:
            self._detect_by_file_extensions(path, result)

        self._detect_env_vars(path, result)
        self._detect_multi_service(path, result)

        return result

    def _analyze_node(self, path: Path, result: AnalysisResult):
        result.language = "javascript"
        pkg_file = path / "package.json"

        try:
            pkg = json.loads(pkg_file.read_text())
        except (json.JSONDecodeError, IOError):
            return

        deps = pkg.get("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        scripts = pkg.get("scripts", {})
        result.dependencies = list(deps.keys())
        result.dev_dependencies = list(dev_deps.keys())

        if "typescript" in dev_deps or (path / "tsconfig.json").exists():
            result.language = "typescript"

        # Framework detection
        if "next" in deps:
            result.framework = "nextjs"
            result.port = 3000
            result.build_command = scripts.get("build", "npm run build")
            result.start_command = scripts.get("start", "npm start")
        elif "nuxt" in deps or "nuxt3" in deps:
            result.framework = "nuxt"
            result.port = 3000
            result.build_command = scripts.get("build", "npm run build")
            result.start_command = scripts.get("start", "node .output/server/index.mjs")
        elif "react" in deps and "vite" in dev_deps:
            result.framework = "react-vite"
            result.port = 5173
            result.build_command = scripts.get("build", "npm run build")
            result.static_output_dir = "dist"
        elif "react" in deps:
            result.framework = "react"
            result.port = 3000
            result.build_command = scripts.get("build", "npm run build")
            result.static_output_dir = "build"
        elif "vue" in deps:
            result.framework = "vue"
            result.port = 5173
            result.build_command = scripts.get("build", "npm run build")
            result.static_output_dir = "dist"
        elif "express" in deps:
            result.framework = "express"
            result.port = 3000
            result.start_command = scripts.get("start", "node index.js")
        elif "fastify" in deps:
            result.framework = "fastify"
            result.port = 3000
            result.start_command = scripts.get("start", "node index.js")
        elif "@hono/node-server" in deps or "hono" in deps:
            result.framework = "hono"
            result.port = 3000
            result.start_command = scripts.get("start", "node index.js")

        # Entry point detection
        if "main" in pkg:
            result.entry_point = pkg["main"]
        elif scripts.get("start"):
            result.entry_point = scripts["start"]

        # Package manager detection
        if (path / "pnpm-lock.yaml").exists():
            result.package_manager = "pnpm"
        elif (path / "yarn.lock").exists():
            result.package_manager = "yarn"
        elif (path / "bun.lockb").exists():
            result.package_manager = "bun"
        else:
            result.package_manager = "npm"

        # Node version detection
        if (path / ".nvmrc").exists():
            result.node_version = (path / ".nvmrc").read_text().strip()
        elif (path / ".node-version").exists():
            result.node_version = (path / ".node-version").read_text().strip()
        elif "engines" in pkg and "node" in pkg["engines"]:
            result.node_version = pkg["engines"]["node"]

    def _analyze_python(self, path: Path, result: AnalysisResult):
        result.language = "python"

        # Package manager
        if (path / "poetry.lock").exists():
            result.package_manager = "poetry"
        elif (path / "Pipfile").exists():
            result.package_manager = "pipenv"
        elif (path / "uv.lock").exists():
            result.package_manager = "uv"
        else:
            result.package_manager = "pip"

        # Gather dependencies
        deps = self._get_python_deps(path)
        result.dependencies = deps

        # Framework detection
        if "fastapi" in deps or "fastapi[all]" in deps:
            result.framework = "fastapi"
            result.port = 8000
            result.start_command = "uvicorn app.main:app --host 0.0.0.0 --port 8000"
            result.entry_point = self._find_python_entry(path, ["app/main.py", "main.py", "src/main.py"])
        elif "flask" in deps:
            result.framework = "flask"
            result.port = 5000
            result.start_command = "gunicorn -w 4 -b 0.0.0.0:5000 app:app"
            result.entry_point = self._find_python_entry(path, ["app.py", "application.py", "wsgi.py"])
        elif "django" in deps:
            result.framework = "django"
            result.port = 8000
            result.start_command = "gunicorn config.wsgi:application --bind 0.0.0.0:8000"
            result.entry_point = self._find_python_entry(path, ["manage.py"])
        elif "streamlit" in deps:
            result.framework = "streamlit"
            result.port = 8501
            result.start_command = "streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
            result.entry_point = self._find_python_entry(path, ["app.py", "main.py", "streamlit_app.py"])
        elif "celery" in deps:
            result.framework = "celery"
            result.start_command = "celery -A tasks worker --loglevel=info"

        # Python version
        pyproject = path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            for line in content.splitlines():
                if "requires-python" in line:
                    result.python_version = line.split("=")[-1].strip().strip('"').strip(">=")
                    break

    def _analyze_go(self, path: Path, result: AnalysisResult):
        result.language = "go"
        result.package_manager = "go modules"
        result.build_command = "go build -o app ."
        result.start_command = "./app"
        result.port = 8080

        go_mod = path / "go.mod"
        if go_mod.exists():
            content = go_mod.read_text()
            for line in content.splitlines():
                if line.startswith("module "):
                    result.entry_point = line.split(" ")[1]
                    break
            # Framework detection from deps
            if "gin-gonic/gin" in content:
                result.framework = "gin"
            elif "labstack/echo" in content:
                result.framework = "echo"
            elif "go-chi/chi" in content:
                result.framework = "chi"
            elif "gofiber/fiber" in content:
                result.framework = "fiber"

    def _analyze_rust(self, path: Path, result: AnalysisResult):
        result.language = "rust"
        result.package_manager = "cargo"
        result.build_command = "cargo build --release"
        result.start_command = "./target/release/app"
        result.port = 8080

        cargo = path / "Cargo.toml"
        if cargo.exists():
            content = cargo.read_text()
            if "actix-web" in content:
                result.framework = "actix-web"
            elif "axum" in content:
                result.framework = "axum"
            elif "rocket" in content:
                result.framework = "rocket"

    def _analyze_java(self, path: Path, result: AnalysisResult):
        result.language = "java"
        result.port = 8080

        if (path / "pom.xml").exists():
            result.package_manager = "maven"
            result.build_command = "mvn clean package -DskipTests"
        elif (path / "build.gradle").exists():
            result.package_manager = "gradle"
            result.build_command = "gradle build -x test"

        # Check for Spring Boot
        pom = path / "pom.xml"
        gradle = path / "build.gradle"
        content = ""
        if pom.exists():
            content = pom.read_text()
        elif gradle.exists():
            content = gradle.read_text()
        if "spring-boot" in content:
            result.framework = "spring-boot"
            result.start_command = "java -jar target/*.jar"

    def _detect_by_file_extensions(self, path: Path, result: AnalysisResult):
        ext_counts: dict[str, int] = {}
        for f in path.rglob("*"):
            if f.is_file() and not any(p in str(f) for p in [".git", "node_modules", "__pycache__", "venv"]):
                ext = f.suffix.lower()
                if ext:
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1

        if not ext_counts:
            return

        top_ext = max(ext_counts, key=ext_counts.get)
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
        }
        result.language = lang_map.get(top_ext, "unknown")

    def _detect_env_vars(self, path: Path, result: AnalysisResult):
        env_example = path / ".env.example"
        if not env_example.exists():
            env_example = path / ".env.sample"
        if not env_example.exists():
            env_example = path / ".env.template"
        if env_example.exists():
            try:
                for line in env_example.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        result.env_vars.append(line.split("=")[0])
            except IOError:
                pass

    def _detect_multi_service(self, path: Path, result: AnalysisResult):
        compose_file = path / "docker-compose.yml"
        if not compose_file.exists():
            compose_file = path / "compose.yml"
        if compose_file.exists():
            try:
                content = compose_file.read_text()
                services = []
                in_services = False
                for line in content.splitlines():
                    if line.strip() == "services:":
                        in_services = True
                        continue
                    if in_services and line and not line.startswith(" ") and not line.startswith("\t"):
                        break
                    if (
                        in_services
                        and line.startswith("  ")
                        and line.strip().endswith(":")
                        and not line.startswith("    ")
                    ):
                        services.append(line.strip().rstrip(":"))
                if len(services) > 1:
                    result.multi_service = True
                    result.services = services
            except IOError:
                pass

    def _get_python_deps(self, path: Path) -> list[str]:
        deps = []
        req_file = path / "requirements.txt"
        if req_file.exists():
            try:
                for line in req_file.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        pkg = (
                            line.split("==")[0]
                            .split(">=")[0]
                            .split("<=")[0]
                            .split("~=")[0]
                            .split("[")[0]
                            .strip()
                            .lower()
                        )
                        if pkg:
                            deps.append(pkg)
            except IOError:
                pass
        return deps

    def _find_python_entry(self, path: Path, candidates: list[str]) -> str | None:
        for candidate in candidates:
            if (path / candidate).exists():
                return candidate
        return None
