"""RCS-50 — stockage POC : CRUD, clés étrangères, alertes et journalisation."""
import csv
import sys
from pathlib import Path

import unittest
try:
    import pytest
except ModuleNotFoundError as exc:
    if exc.name != 'pytest':
        raise
    raise unittest.SkipTest('Suite RCS-50 exécutée par sa CI dédiée') from exc

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rcs import alerts as A  # noqa: E402
from rcs.db import connect  # noqa: E402
from rcs.ingestion import CONTRACT, import_csv  # noqa: E402

HEADER = list(CONTRACT) + ["Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"]

def _row(udi, typ="M", air=298.1, proc=308.6, rpm=1551, torque=42.8, wear=0, fail=0):
    return {"UDI": udi, "Type": typ, "Air temperature [K]": air, "Process temperature [K]": proc,
            "Rotational speed [rpm]": rpm, "Torque [Nm]": torque, "Tool wear [min]": wear,
            "Machine failure": fail, "Product ID": f"P{udi}", "TWF": 0, "HDF": 0, "PWF": 0, "OSF": 0, "RNF": 0}


def _write(path: Path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    return path


@pytest.fixture
def conn():
    c = connect(":memory:")
    c.execute("INSERT INTO utilisateur VALUES ('tech-01','T','technicien'),('obs-01','O','admin')")
    try:
        yield c
    finally:
        c.close()


def test_foreign_keys_enforced(conn):
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO alerte(analyse_id, equipement_id, gravite, cree_le) VALUES (999,'X','info','t')")


def test_alert_workflow_unique_and_human_review(conn, tmp_path):
    import_csv(conn, _write(tmp_path / "a.csv", [_row(1)]))
    obs = conn.execute("SELECT id FROM observation").fetchone()["id"]
    _, a1 = A.enregistrer_analyse(conn, obs, "m@v1", score=5.0, seuil=2.0)
    _, a2 = A.enregistrer_analyse(conn, obs, "m@v1", score=5.0, seuil=2.0)  # rejeu
    assert a1 == a2 and conn.execute("SELECT COUNT(*) FROM alerte").fetchone()[0] == 1
    assert conn.execute("SELECT gravite FROM alerte").fetchone()[0] == "critique"

    with pytest.raises(A.TransitionInvalide):
        A.ouvrir_intervention(conn, a1, "tech-01")       # pas encore validée
    with pytest.raises(A.PermissionRefusee):
        A.decider_alerte(conn, a1, "obs-01", "validee")  # rôle non habilité
    A.decider_alerte(conn, a1, "tech-01", "validee", "ok")
    with pytest.raises(A.TransitionInvalide):
        A.decider_alerte(conn, a1, "tech-01", "rejetee")  # décision unique
    assert A.ouvrir_intervention(conn, a1, "tech-01") > 0
    events = [r[0] for r in conn.execute("SELECT evenement FROM audit")]
    assert "alerte_validee" in events and "decision_refusee_permission" in events


def test_below_threshold_creates_no_alert(conn, tmp_path):
    import_csv(conn, _write(tmp_path / "a.csv", [_row(1)]))
    obs = conn.execute("SELECT id FROM observation").fetchone()["id"]
    _, alerte = A.enregistrer_analyse(conn, obs, "m@v1", score=1.0, seuil=2.0)
    assert alerte is None


def test_decision_persists_actor_timestamp_and_audit(conn, tmp_path):
    import_csv(conn, _write(tmp_path / "b.csv", [_row(1)]))
    obs = conn.execute("SELECT id FROM observation").fetchone()["id"]
    _, alert = A.enregistrer_analyse(conn, obs, "m@v1", score=5, seuil=2)
    A.decider_alerte(conn, alert, "tech-01", "rejetee")
    row = conn.execute("SELECT statut, decide_par, decide_le FROM alerte WHERE id=?", (alert,)).fetchone()
    assert row["statut"] == "rejetee" and row["decide_par"] == "tech-01" and row["decide_le"]
    with pytest.raises(A.TransitionInvalide):
        A.ouvrir_intervention(conn, alert, "tech-01")
