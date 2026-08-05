"""Tests for the code analyzer module."""

import json
import os
import tempfile

import pytest

from forgepipeline_ai.analyzer import AnalysisResult, CodeAnalyzer


@pytest.fixture
def analyzer():
    return CodeAnalyzer()


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary directory simulating a repo."""
    return tmp_path


class TestCodeAnalyzer:
    def test_analyze_nonexistent_path(self, analyzer):
        with pytest.raises(ValueError, match="does not exist"):
            analyzer.analyze("/nonexistent/path")

    def test_detect_python_pip(self, analyzer, tmp_repo):
        (tmp_repo / "requirements.txt").write_text("flask==3.0.0\nredis\n")
        result = analyzer.analyze(str(tmp_repo))
        assert result.language == "python"
        assert result.framework == "flask"
        assert result.package_manager == "pip"
        assert result.port == 5000
        assert "flask" in result.dependencies

    def test_detect_python_fastapi(self, analyzer, tmp_repo):
        (tmp_repo / "requirements.txt").write_text("fastapi\nuvicorn\n")
        (tmp_repo / "app").mkdir()
        (tmp_repo / "app" / "main.py").write_text("from fastapi import FastAPI")
        result = analyzer.analyze(str(tmp_repo))
        assert result.framework == "fastapi"
        assert result.port == 8000
        assert result.entry_point == "app/main.py"

    def test_detect_python_django(self, analyzer, tmp_repo):
        (tmp_repo / "requirements.txt").write_text("django\n")
        (tmp_repo / "manage.py").write_text("")
        result = analyzer.analyze(str(tmp_repo))
        assert result.framework == "django"
        assert result.port == 8000

    def test_detect_node_express(self, analyzer, tmp_repo):
        pkg = {
            "name": "test",
            "dependencies": {"express": "^4.18.0"},
            "scripts": {"start": "node server.js"},
        }
        (tmp_repo / "package.json").write_text(json.dumps(pkg))
        result = analyzer.analyze(str(tmp_repo))
        assert result.language == "javascript"
        assert result.framework == "express"
        assert result.port == 3000

    def test_detect_node_typescript(self, analyzer, tmp_repo):
        pkg = {
            "name": "test",
            "dependencies": {"next": "^14.0.0"},
            "devDependencies": {"typescript": "^5.0.0"},
            "scripts": {"build": "next build", "start": "next start"},
        }
        (tmp_repo / "package.json").write_text(json.dumps(pkg))
        result = analyzer.analyze(str(tmp_repo))
        assert result.language == "typescript"
        assert result.framework == "nextjs"

    def test_detect_react_vite(self, analyzer, tmp_repo):
        pkg = {
            "name": "test",
            "dependencies": {"react": "^18.0.0"},
            "devDependencies": {"vite": "^5.0.0"},
            "scripts": {"build": "vite build"},
        }
        (tmp_repo / "package.json").write_text(json.dumps(pkg))
        result = analyzer.analyze(str(tmp_repo))
        assert result.framework == "react-vite"
        assert result.static_output_dir == "dist"

    def test_detect_go(self, analyzer, tmp_repo):
        (tmp_repo / "go.mod").write_text("module github.com/user/app\n\ngo 1.22\n")
        result = analyzer.analyze(str(tmp_repo))
        assert result.language == "go"
        assert result.package_manager == "go modules"
        assert result.port == 8080

    def test_detect_go_gin(self, analyzer, tmp_repo):
        (tmp_repo / "go.mod").write_text(
            "module github.com/user/app\n\ngo 1.22\n\nrequire github.com/gin-gonic/gin v1.9.0\n"
        )
        result = analyzer.analyze(str(tmp_repo))
        assert result.framework == "gin"

    def test_detect_rust(self, analyzer, tmp_repo):
        (tmp_repo / "Cargo.toml").write_text('[package]\nname = "app"\n\n[dependencies]\naxum = "0.7"\n')
        result = analyzer.analyze(str(tmp_repo))
        assert result.language == "rust"
        assert result.framework == "axum"
        assert result.package_manager == "cargo"

    def test_detect_java_maven_spring(self, analyzer, tmp_repo):
        (tmp_repo / "pom.xml").write_text("<project><dependency>spring-boot</dependency></project>")
        result = analyzer.analyze(str(tmp_repo))
        assert result.language == "java"
        assert result.framework == "spring-boot"
        assert result.package_manager == "maven"

    def test_detect_dockerfile(self, analyzer, tmp_repo):
        (tmp_repo / "Dockerfile").write_text("FROM python:3.12\n")
        (tmp_repo / "requirements.txt").write_text("flask\n")
        result = analyzer.analyze(str(tmp_repo))
        assert result.has_dockerfile is True

    def test_detect_env_vars(self, analyzer, tmp_repo):
        (tmp_repo / ".env.example").write_text("DATABASE_URL=\nSECRET_KEY=\n# Comment\n")
        (tmp_repo / "requirements.txt").write_text("flask\n")
        result = analyzer.analyze(str(tmp_repo))
        assert "DATABASE_URL" in result.env_vars
        assert "SECRET_KEY" in result.env_vars

    def test_detect_package_manager_pnpm(self, analyzer, tmp_repo):
        pkg = {"name": "test", "dependencies": {"express": "^4.0"}}
        (tmp_repo / "package.json").write_text(json.dumps(pkg))
        (tmp_repo / "pnpm-lock.yaml").write_text("")
        result = analyzer.analyze(str(tmp_repo))
        assert result.package_manager == "pnpm"

    def test_empty_repo_unknown_language(self, analyzer, tmp_repo):
        result = analyzer.analyze(str(tmp_repo))
        assert result.language == "unknown"
