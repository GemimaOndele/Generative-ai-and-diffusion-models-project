"""RCS-42 — MLD/SQL : migrations versionnées, clés étrangères, contraintes CHECK/UNIQUE."""
import sqlite3
import sys
from pathlib import Path

import unittest
try:
    import pytest
except ModuleNotFoundError as exc:
    if exc.name != 'pytest':
        raise
    raise unittest.SkipTest('Suite SQL exécutée par le workflow RCS-42 avec pytest') from exc

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rcs.db import connect  # noqa: E402


@pytest.fixture
def conn():
    c = connect(":memory:")
    try:
        yield c
    finally:
        c.close()


def test_migrations_versioned_and_applied_once(tmp_path):
    db = tmp_path / "m.sqlite"
    connect(db).close()
    c = connect(db)
    assert [r[0] for r in c.execute("SELECT version FROM schema_migrations")] == ["001_init_schema.sql"]
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    c.close()
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


def _alert_fixture(c):
    c.execute("INSERT INTO source_donnees VALUES ('S','n','u','l','c','d')")
    c.execute("INSERT INTO lot_import(source_id,fichier,sha256,nb_lignes,nb_acceptees,nb_rejetees,nb_doublons,importe_le) VALUES ('S','f','h',1,1,0,0,'t')")
    c.execute("INSERT INTO equipement(id,type) VALUES ('E1','t'),('E2','t')")
    c.execute("INSERT INTO observation(equipement_id,lot_id,cle_source,air_temp_k,process_temp_k,rpm,torque_nm,tool_wear_min,label,label_origine) VALUES ('E1',1,'1',300,310,1000,40,0,0,'synthetic'),('E2',1,'2',300,310,1000,40,0,0,'synthetic')")
    c.execute("INSERT INTO analyse_modele(observation_id,model_version,score,seuil,cree_le) VALUES (1,'v1',2,1,'t')")
    c.execute("INSERT INTO utilisateur VALUES ('U','demo','technicien')")


def test_alert_equipment_consistency(conn):
    _alert_fixture(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO alerte(analyse_id,equipement_id,gravite,cree_le) VALUES (1,'E2','info','t')")
    conn.execute("INSERT INTO alerte(analyse_id,equipement_id,gravite,cree_le) VALUES (1,'E1','info','t')")
    for query in ("UPDATE alerte SET equipement_id='E2'", "UPDATE observation SET equipement_id='E2' WHERE id=1", "UPDATE analyse_modele SET observation_id=2"):
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(query)


def test_terminal_decision_requires_actor_and_timestamp(conn):
    _alert_fixture(conn)
    conn.execute("INSERT INTO alerte(analyse_id,equipement_id,gravite,cree_le) VALUES (1,'E1','info','t')")
    for query in ("UPDATE alerte SET statut='validee'", "UPDATE alerte SET statut='rejetee',decide_par='U'", "UPDATE alerte SET statut='validee',decide_par='U',decide_le=''"):
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(query)
    conn.execute("UPDATE alerte SET statut='validee',decide_par='U',decide_le='2026-11-24T09:00:00Z'")


def test_metric_split_required_and_unique(conn):
    conn.execute("INSERT INTO experiment_run(jalon,config,cree_le) VALUES ('J1','{}','t')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO experiment_metric(run_id,nom,split) VALUES (1,'f1',NULL)")
    conn.execute("INSERT INTO experiment_metric(run_id,nom,split) VALUES (1,'f1','test')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO experiment_metric(run_id,nom,split) VALUES (1,'f1','test')")
