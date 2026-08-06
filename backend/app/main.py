"""ForgePipeline AI Backend API."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .middleware import api_key_middleware
from .routers import projects, tasks, containers, users, deployments, artifacts

CORS_ORIGINS = os.environ.get(
    "FORGE_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ForgePipeline AI",
    description="Agentic cloud deployment API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(api_key_middleware)

app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(containers.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(deployments.router, prefix="/api")
app.include_router(artifacts.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "forgepipeline-ai"}
