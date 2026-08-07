"""Tests for the intent parser module."""

import pytest

from forgepipeline_ai.intent_parser import IntentParser


@pytest.fixture
def parser():
    return IntentParser()


class TestStructuredParsing:
    def test_basic_deploy(self, parser):
        result = parser.parse(repo="https://github.com/user/app", target="aws-ecs", env="staging")
        assert result["source_repo"] == "https://github.com/user/app"
        assert result["target_platform"] == "aws-ecs"
        assert result["environment"] == "staging"

    def test_target_alias_ecs(self, parser):
        result = parser.parse(repo="https://github.com/u/a", target="ecs")
        assert result["target_platform"] == "aws-ecs"

    def test_target_alias_k8s(self, parser):
        result = parser.parse(repo="https://github.com/u/a", target="k8s")
        assert result["target_platform"] == "kubernetes"

    def test_target_alias_gcp(self, parser):
        result = parser.parse(repo="https://github.com/u/a", target="gcp")
        assert result["target_platform"] == "gcp-run"

    def test_env_alias_prod(self, parser):
        result = parser.parse(repo="https://github.com/u/a", target="ecs", env="prod")
        assert result["environment"] == "production"

    def test_env_alias_dev(self, parser):
        result = parser.parse(repo="https://github.com/u/a", target="ecs", env="dev")
        assert result["environment"] == "development"

    def test_no_docker_flag(self, parser):
        result = parser.parse(repo="https://github.com/u/a", target="ecs", no_docker=True)
        assert "no_docker" not in result or result.get("no_docker") is True

    def test_registry_option(self, parser):
        registry = "123456.dkr.ecr.us-east-1.amazonaws.com"
        result = parser.parse(
            repo="https://github.com/u/a", target="ecs", registry=registry,
        )
        assert result["registry_url"] == registry


class TestNaturalLanguageParsing:
    def test_deploy_to_ecs(self, parser):
        result = parser.parse(natural_language="deploy https://github.com/user/app to ecs in production")
        assert result["action"] == "deploy"
        assert result["source_repo"] == "https://github.com/user/app"
        assert result["target_platform"] == "aws-ecs"
        assert result["environment"] == "production"

    def test_rollback_action(self, parser):
        result = parser.parse(natural_language="rollback the last deployment")
        assert result["action"] == "rollback"

    def test_status_action(self, parser):
        result = parser.parse(natural_language="check health of the service")
        assert result["action"] == "status"

    def test_destroy_action(self, parser):
        result = parser.parse(natural_language="teardown the staging environment")
        assert result["action"] == "destroy"

    def test_extract_region(self, parser):
        result = parser.parse(natural_language="deploy to ecs in us-west-2")
        assert result["region"] == "us-west-2"

    def test_kubernetes_alias(self, parser):
        result = parser.parse(natural_language="deploy to kubernetes in staging")
        assert result["target_platform"] == "kubernetes"

    def test_cloud_run_alias(self, parser):
        result = parser.parse(natural_language="deploy to cloud run")
        assert result["target_platform"] == "gcp-run"
