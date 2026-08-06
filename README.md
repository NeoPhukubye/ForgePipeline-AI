# ForgePipeline AI

[![CI](https://github.com/NeoPhukubye/ForgePipeline-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/NeoPhukubye/ForgePipeline-AI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An agentic cloud application that automates Docker containerization and cloud deployment workflows.

---

**ForgePipeline AI** is an intelligent system designed to streamline the DevOps lifecycle. By leveraging AI agents, it understands high-level user goals, automatically analyzes source code, generates optimized Dockerfiles, and orchestrates complex deployment pipelines to various cloud providers.

The goal is to move from imperative commands to declarative intent. Instead of writing lengthy CI/CD scripts, you simply tell the agent what you want to achieve: *"Deploy the latest version of my web service to the staging environment on AWS."*

## Key Features

- **Agentic Workflow Automation**: An AI agent that can reason, plan, and execute deployment tasks from start to finish.
- **Smart Code Analysis**: Automatically inspects your repository to determine the language, framework, and dependencies, ensuring an optimal containerization strategy.
- **Dockerfile Generation**: Creates efficient, secure, and multi-stage Dockerfiles without manual intervention.
- **Multi-Cloud Deployment**: Abstracted deployment engine with support for AWS ECS, Google Cloud Run, Azure Container Apps, Kubernetes, and AWS Lambda.
- **Natural Language Interface**: Interact with your deployment pipeline using conversational commands (future goal).
- **Self-Correction & Rollbacks**: The agent can detect deployment failures and automatically initiate a rollback to a last known good state.
- **Web Dashboard**: React-based UI for monitoring projects, deployments, and containers in real time.

## Architecture

ForgePipeline AI is composed of several core components:

1.  **Intent Parser**: Interprets user commands and goals.
2.  **Planning Agent**: Breaks down the goal into a sequence of executable steps (e.g., clone repo, analyze code, generate Dockerfile, build image, push to registry, deploy).
3.  **Execution Engine**: Carries out the steps planned by the agent, interacting with tools like Docker, Git, and cloud provider APIs.
4.  **Knowledge Base**: Stores information about cloud services, best practices, and past deployments to improve future performance.
5.  **FastAPI Backend**: REST API for project/task/deployment management with SQLite persistence.
6.  **React Dashboard**: Vite + React + Tailwind frontend for pipeline visibility.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker

### Installation

```bash
# Clone the repository
git clone https://github.com/NeoPhukubye/ForgePipeline-AI.git
cd ForgePipeline-AI

# Install the Python CLI + core
pip install -e ".[backend,dev]"

# Install frontend dependencies
npm install

# Copy environment config
cp .env.example .env
```

### Usage

```bash
# CLI: Deploy a repo
forgepipeline deploy --repo https://github.com/user/my-app --target aws-ecs --env staging

# CLI: Analyze a local project
forgepipeline analyze ./my-project

# CLI: Generate a Dockerfile
forgepipeline generate ./my-project -o Dockerfile

# Start the backend API
uvicorn backend.app.main:app --reload

# Start the frontend dev server
npm run dev
```

### Running Tests

```bash
# Python core tests
pytest tests/

# Backend API tests
pytest backend/tests/

# Frontend type-check
npm run typecheck
```
