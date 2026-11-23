"""RCS-38 — API locale de démonstration, sans équipement ni patient réel.

Python standard library uniquement. Serveur lié à 127.0.0.1. Le rôle
"technicien-demo" est une SIMULATION, pas une authentification réelle.
Les données fictives sont identifiées par fictional_demo_only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
import tempfile
from urllib.parse import urlsplit
from uuid import uuid4

from tools.rcs38_contract import validate_fixture

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "frontend" / "monitoring"
FIXTURE = FRONT / "demo.json"
ALLOWED_DECISIONS = {
    "approved": {"controle_confirme"},
    "rejected": {"signal_non_confirme", "qualite_insuffisante"},
}
ACTION_ID = re.compile(r"^ACT-DEMO-[A-Z0-9-]{1,30}$")
ACTION_PATH = re.compile(r"^/api/v1/demo/actions/(ACT-DEMO-[A-Z0-9-]{1,30})/decision$")
DATA_MODE = "fictional_demo_only"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_fixture(path: Path = FIXTURE) -> dict:
    validate_fixture(path)
    raw = path.read_bytes()
    fixture = json.loads(raw)
    if fixture.get("data_mode") != DATA_MODE:
        raise ValueError("Seules les fixtures explicitement fictives sont autorisées.")
    for key in ("devices", "readings", "actions", "runs"):
        if not isinstance(fixture.get(key), list):
            raise ValueError(f"Collection de démonstration manquante : {key}")
    fixture["_fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    return fixture


class DemoStore:
    """Petite base SQLite isolée pour conserver les décisions *simulées*."""
    def __init__(self, path: Path, fixture: dict):
        self.path = Path(path)
        self.fixture = fixture
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        con = sqlite3.connect(str(self.path), timeout=5)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def _initialize(self):
        con = self._connect()
        try:
            with con:
                con.executescript("""
                CREATE TABLE IF NOT EXISTS demo_actions (
                    id TEXT PRIMARY KEY,
                    device TEXT NOT NULL,
                    site TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'En attente',
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS demo_events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL UNIQUE,
                    action_id TEXT NOT NULL REFERENCES demo_actions(id),
                    decision TEXT NOT NULL,
                    reason_code TEXT NOT NULL,
                    before_state TEXT NOT NULL,
                    after_state TEXT NOT NULL,
                    actor_role TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """)
                for action in self.fixture["actions"]:
                    if not ACTION_ID.fullmatch(action["id"]):
                        raise ValueError("Identifiant d'action fictive invalide")
                    con.execute(
                        "INSERT OR IGNORE INTO demo_actions "
                        "(id,device,site,reason,state) VALUES (?,?,?,?,?)",
                        (action["id"], action["device"], action["site"],
                         action["reason"], "En attente")
                    )
        finally:
            con.close()

    def actions(self) -> list[dict]:
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT id,device,site,reason,state,updated_at "
                "FROM demo_actions ORDER BY id"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            con.close()

    def events(self) -> list[dict]:
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT trace_id,action_id,decision,reason_code,"
                "before_state,after_state,actor_role,created_at "
                "FROM demo_events ORDER BY seq DESC LIMIT 100"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            con.close()

    def decide(self, action_id: str, decision: str, reason_code: str) -> dict:
        if not ACTION_ID.fullmatch(action_id):
            raise ValueError("Identifiant d'action invalide")
        if decision not in ALLOWED_DECISIONS or reason_code not in ALLOWED_DECISIONS[decision]:
            raise ValueError("Décision ou motif non autorisé")
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT state FROM demo_actions WHERE id=?", (action_id,)).fetchone()
            if row is None:
                con.rollback()
                raise KeyError("Action fictive introuvable")
            if row["state"] != "En attente":
                con.rollback()
                raise RuntimeError("Action déjà traitée : conflit d'état")
            new_state = "Approuvée" if decision == "approved" else "Rejetée"
            when, trace = utc_now(), str(uuid4())
            con.execute(
                "UPDATE demo_actions SET state=?,updated_at=? WHERE id=?",
                (new_state, when, action_id),
            )
            con.execute(
                "INSERT INTO demo_events "
                "(trace_id,action_id,decision,reason_code,before_state,"
                "after_state,actor_role,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (trace, action_id, decision, reason_code, "En attente",
                 new_state, "technicien-demo", when),
            )
            con.commit()
            return {
                "trace_id": trace, "action_id": action_id,
                "state": new_state, "decision": decision,
                "reason_code": reason_code, "created_at": when,
                "actor_role": "technicien-demo",
                "data_mode": DATA_MODE,
            }
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()


def make_handler(store: DemoStore):
    fixture = store.fixture

    class DemoHandler(SimpleHTTPRequestHandler):
        """Sert SEULEMENT frontend/monitoring et API fictive, sans CORS."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(FRONT), **kwargs)

        def _headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; img-src 'self' data:; "
                "object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
            )

        def _json(self, status: int, content: dict):
            payload = json.dumps(content, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self._headers()
            self.end_headers()
            self.wfile.write(payload)

        def end_headers(self):
            # Static HTML/CSS/JS also receive security and cache headers.
            if not self.path.startswith("/api/"):
                self._headers()
            super().end_headers()

        def do_GET(self):
            if not self._local_host():
                return self._json(403, {"error": "Hôte local obligatoire"})
            path = urlsplit(self.path).path
            if path == "/api/v1/demo/health":
                return self._json(200, {
                    "status": "demo_only", "data_mode": DATA_MODE,
                    "version": "rcs38-local-api-v1",
                })
            if path == "/api/v1/demo/overview":
                return self._json(200, {
                    **fixture, "actions": store.actions(),
                    "events": store.events(), "server_mode": "local_demo",
                    "api_version": "v1", "measurement_status": "fictional",
                })
            if path.startswith("/api/"):
                return self._json(404, {"error": "Endpoint inconnu"})
            if path == "/":
                self.send_response(302)
                self.send_header("Location", "/index.html")
                self.end_headers()
                return
            return super().do_GET()

        def do_HEAD(self):
            if not self._local_host():
                self.send_response(403)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return super().do_HEAD()

        def _local_host(self):
            port = self.server.server_address[1]
            return self.headers.get("Host") in {
                f"127.0.0.1:{port}", f"localhost:{port}"
            }

        def do_POST(self):
            if not self._local_host():
                return self._json(403, {"error": "Hôte local obligatoire"})
            path = urlsplit(self.path).path
            match = ACTION_PATH.fullmatch(path)
            if not match:
                return self._json(404, {"error": "Action d'API inconnue"})
            origin = self.headers.get("Origin")
            port = self.server.server_address[1]
            allowed_origins = {
                f"http://127.0.0.1:{port}", f"http://localhost:{port}"
            }
            if origin and origin not in allowed_origins:
                return self._json(403, {"error": "Origine non autorisée"})
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                return self._json(403, {"error": "Requête cross-site refusée"})
            if self.headers.get_content_type() != "application/json":
                return self._json(415, {"error": "Content-Type application/json obligatoire"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if not 1 <= length <= 1024:
                return self._json(413, {"error": "Taille de requête invalide"})
            try:
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Objet JSON attendu")
                if set(body) != {"decision", "reason_code", "acknowledge_simulation"}:
                    raise ValueError("Champs JSON inattendus")
                if body["acknowledge_simulation"] is not True:
                    raise ValueError("Confirmation du mode simulation obligatoire")
                result = store.decide(match.group(1), body["decision"], body["reason_code"])
                return self._json(200, result)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                return self._json(400, {"error": str(exc)})
            except KeyError:
                return self._json(404, {"error": "Action inconnue"})
            except RuntimeError as exc:
                return self._json(409, {"error": str(exc)})

        def log_message(self, format_string, *args):
            # Journal d'accès limité au serveur local ; aucune donnée patient.
            return

    return DemoHandler


def build_server(port: int = 8000, db_path: Path | None = None,
                 fixture_path: Path = FIXTURE) -> ThreadingHTTPServer:
    if db_path is None:
        db_path = Path(tempfile.gettempdir()) / "robocare-rcs38-local-demo.sqlite3"
    store = DemoStore(db_path, load_fixture(fixture_path))
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(store))


def main():
    parser = argparse.ArgumentParser(description="RCS-38 : backend local fictif")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", type=Path, default=None,
                        help="Chemin de base SQLite locale, ignorée par Git")
    args = parser.parse_args()
    server = build_server(port=args.port, db_path=args.db)
    print(f"RoboCare Sentinel DEMO — http://127.0.0.1:{server.server_address[1]}/", flush=True)
    print("Simulation locale : aucun accès patient, machine ou LLM.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
