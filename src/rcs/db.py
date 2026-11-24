"""Stockage POC (SQLite) — tables métier + couche expériences.

Le DDL est versionné dans sql/NNN_*.sql (migrations). Schéma dérivé des entités candidates de la Bibliothèque V3 §8.1/§8.2. Le MCD JMerise officiel reste
à produire par le référent BDD ; ce script en est une implémentation provisoire (docs/db_schema.md).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"


def load_migrations() -> list[tuple[str, str]]:
    """Migrations SQL versionnées, appliquées dans l'ordre (sql/NNN_*.sql)."""
    return [(p.name, p.read_text(encoding="utf-8")) for p in sorted(SQL_DIR.glob("[0-9][0-9][0-9]_*.sql"))]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
    for name, sql in load_migrations():
        if name not in done:
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_migrations VALUES (?, ?)", (name, utc_now()))
            conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def audit(conn: sqlite3.Connection, acteur: str, evenement: str, cible: str) -> None:
    conn.execute(
        "INSERT INTO audit(acteur, evenement, cible, horodatage) VALUES (?,?,?,?)",
        (acteur, evenement, cible, utc_now()),
    )
