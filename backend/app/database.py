"""Database setup using SQLite for local development."""

import os
import sqlite3
from contextlib import contextmanager


def _db_path() -> str:
    return os.environ.get("FORGE_DB_PATH", "forge_pipeline.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                source_repo_url TEXT NOT NULL,
                cloud_provider TEXT,
                deployment_target TEXT,
                deployment_region TEXT,
                environment TEXT DEFAULT 'staging',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                task_type TEXT NOT NULL CHECK (task_type IN ('CONTAINERIZE', 'DEPLOY', 'ANALYZE')),
                status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')),
                started_at TEXT,
                completed_at TEXT,
                duration_seconds REAL,
                error_message TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                timestamp TEXT DEFAULT (datetime('now')),
                level TEXT NOT NULL DEFAULT 'INFO' CHECK (level IN ('INFO', 'WARN', 'ERROR', 'DEBUG')),
                message TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                artifact_type TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS containers (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                task_id TEXT REFERENCES tasks(id),
                name TEXT NOT NULL,
                image_uri TEXT NOT NULL,
                tag TEXT NOT NULL DEFAULT 'latest',
                size_bytes INTEGER,
                pushed_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT 'developer' CHECK (role IN ('admin', 'developer', 'viewer')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS deployments (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                task_id TEXT REFERENCES tasks(id),
                environment TEXT NOT NULL DEFAULT 'staging',
                cloud_provider TEXT,
                region TEXT,
                status TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN (
                        'PENDING', 'IN_PROGRESS', 'LIVE',
                        'ROLLED_BACK', 'FAILED'
                    )),
                deployed_by TEXT REFERENCES users(id),
                deployed_at TEXT,
                url TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
