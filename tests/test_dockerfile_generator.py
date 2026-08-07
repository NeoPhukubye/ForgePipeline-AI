"""Tests for the Dockerfile generator module."""

import pytest

from forgepipeline_ai.analyzer import AnalysisResult
from forgepipeline_ai.dockerfile_generator import DockerfileGenerator


@pytest.fixture
def generator():
    return DockerfileGenerator()


class TestDockerfileGenerator:
    def test_python_fastapi(self, generator):
        analysis = AnalysisResult(
            language="python",
            framework="fastapi",
            package_manager="pip",
            port=8000,
            start_command="uvicorn app.main:app --host 0.0.0.0 --port 8000",
        )
        dockerfile = generator.generate(analysis)
        assert "FROM python:" in dockerfile
        assert "EXPOSE 8000" in dockerfile
        assert "requirements.txt" in dockerfile
        assert "USER app" in dockerfile

    def test_python_poetry(self, generator):
        analysis = AnalysisResult(
            language="python",
            framework="fastapi",
            package_manager="poetry",
            port=8000,
            start_command="uvicorn app.main:app --host 0.0.0.0",
        )
        dockerfile = generator.generate(analysis)
        assert "poetry" in dockerfile
        assert "pyproject.toml" in dockerfile

    def test_python_uv(self, generator):
        analysis = AnalysisResult(
            language="python",
            framework="fastapi",
            package_manager="uv",
            port=8000,
            start_command="uvicorn app.main:app",
        )
        dockerfile = generator.generate(analysis)
        assert "uv" in dockerfile
        assert "uv.lock" in dockerfile

    def test_node_static_react_vite(self, generator):
        analysis = AnalysisResult(
            language="typescript",
            framework="react-vite",
            package_manager="npm",
            port=5173,
            static_output_dir="dist",
            build_command="npm run build",
        )
        dockerfile = generator.generate(analysis)
        assert "nginx" in dockerfile
        assert "EXPOSE 80" in dockerfile
        assert "/usr/share/nginx/html" in dockerfile

    def test_node_server_express(self, generator):
        analysis = AnalysisResult(
            language="javascript",
            framework="express",
            package_manager="npm",
            port=3000,
            start_command="node server.js",
        )
        dockerfile = generator.generate(analysis)
        assert "FROM node:" in dockerfile
        assert "EXPOSE 3000" in dockerfile
        assert "node" in dockerfile

    def test_go(self, generator):
        analysis = AnalysisResult(language="go", port=8080)
        dockerfile = generator.generate(analysis)
        assert "FROM golang:" in dockerfile
        assert "CGO_ENABLED=0" in dockerfile
        assert "FROM scratch" in dockerfile
        assert "EXPOSE 8080" in dockerfile

    def test_rust(self, generator):
        analysis = AnalysisResult(language="rust", framework="axum", port=8080)
        dockerfile = generator.generate(analysis)
        assert "FROM rust:" in dockerfile
        assert "cargo build --release" in dockerfile
        assert "USER app" in dockerfile

    def test_java_maven(self, generator):
        analysis = AnalysisResult(language="java", framework="spring-boot", package_manager="maven", port=8080)
        dockerfile = generator.generate(analysis)
        assert "maven" in dockerfile
        assert "java -jar" in dockerfile.lower() or '["java"' in dockerfile

    def test_unknown_language_generic(self, generator):
        analysis = AnalysisResult(language="unknown")
        dockerfile = generator.generate(analysis)
        assert "FROM ubuntu:" in dockerfile

    def test_pnpm_lockfile(self, generator):
        analysis = AnalysisResult(
            language="typescript",
            framework="nextjs",
            package_manager="pnpm",
            port=3000,
            start_command="npm start",
            build_command="npm run build",
        )
        dockerfile = generator.generate(analysis)
        assert "pnpm" in dockerfile
