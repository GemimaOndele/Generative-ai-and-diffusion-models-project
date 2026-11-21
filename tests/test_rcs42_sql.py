"""RCS-42 — MLD/SQL : migrations versionnées, clés étrangères, contraintes CHECK/UNIQUE."""
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rcs.db import connect  # noqa: E402


@pytest.fixture
def conn():
    return connect(":memory:")


def test_migrations_versioned_and_applied_once(tmp_path):
    db = tmp_path / "m.sqlite"
    connect(db).close()
    c = connect(db)
    assert [r[0] for r in c.execute("SELECT version FROM schema_migrations")] == ["001_init_schema.sql"]
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"source_donnees", "lot_import", "equipement", "observation", "analyse_modele", "alerte",
            "intervention", "utilisateur", "audit", "experiment_run", "experiment_metric"} <= tables


def test_foreign_keys_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO alerte(analyse_id, equipement_id, gravite, cree_le) VALUES (999,'X','info','t')")


def test_check_constraints(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO utilisateur VALUES ('x','X','pirate')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO equipement(id, type, criticite) VALUES ('E','t','extreme')")


def test_unique_lot_hash(conn):
    conn.execute("INSERT INTO source_donnees VALUES ('S','n','u','l','c','d')")
    conn.execute("INSERT INTO lot_import(source_id,fichier,sha256,nb_lignes,nb_acceptees,nb_rejetees,nb_doublons,importe_le)"
                 " VALUES ('S','f','h',1,1,0,0,'t')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO lot_import(source_id,fichier,sha256,nb_lignes,nb_acceptees,nb_rejetees,nb_doublons,importe_le)"
                     " VALUES ('S','g','h',1,1,0,0,'t')")
