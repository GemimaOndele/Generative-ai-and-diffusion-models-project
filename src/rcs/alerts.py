"""Alertes avec revue humaine (flux F4/F5).

Règles : une analyse produit au plus une alerte (idempotence) ; seule une personne habilitée
(technicien/responsable) valide ou rejette ; toute décision est horodatée et auditée ; une
intervention ne peut être ouverte que sur une alerte validée. Aucune action sur machine réelle.
"""
from __future__ import annotations

import sqlite3

from .db import audit, utc_now

ROLES_HABILITES = {"technicien", "responsable"}


class PermissionRefusee(Exception):
    pass


class TransitionInvalide(Exception):
    pass


def gravite(score: float, seuil: float) -> str:
    if score >= 2 * seuil:
        return "critique"
    if score >= seuil:
        return "attention"
    return "info"


def enregistrer_analyse(conn: sqlite3.Connection, observation_id: int, model_version: str,
                        score: float, seuil: float) -> tuple[int, int | None]:
    """Enregistre un score ; crée une alerte si score >= seuil. Rejouable sans doublon."""
    conn.execute(
        "INSERT OR IGNORE INTO analyse_modele(observation_id, model_version, score, seuil, cree_le) VALUES (?,?,?,?,?)",
        (observation_id, model_version, score, seuil, utc_now()),
    )
    analyse = conn.execute(
        "SELECT id, score, seuil FROM analyse_modele WHERE observation_id=? AND model_version=?",
        (observation_id, model_version),
    ).fetchone()
    alerte_id = None
    if analyse["score"] >= analyse["seuil"]:
        eq = conn.execute("SELECT equipement_id FROM observation WHERE id=?", (observation_id,)).fetchone()
        conn.execute(
            "INSERT OR IGNORE INTO alerte(analyse_id, equipement_id, gravite, cree_le) VALUES (?,?,?,?)",
            (analyse["id"], eq["equipement_id"], gravite(analyse["score"], analyse["seuil"]), utc_now()),
        )
        alerte_id = conn.execute("SELECT id FROM alerte WHERE analyse_id=?", (analyse["id"],)).fetchone()["id"]
    conn.commit()
    return analyse["id"], alerte_id


def _role(conn: sqlite3.Connection, user_id: str) -> str | None:
    r = conn.execute("SELECT role FROM utilisateur WHERE id=?", (user_id,)).fetchone()
    return r["role"] if r else None


def decider_alerte(conn: sqlite3.Connection, alerte_id: int, user_id: str, decision: str,
                   commentaire: str = "") -> None:
    if decision not in {"validee", "rejetee"}:
        raise ValueError("decision doit être 'validee' ou 'rejetee'")
    if _role(conn, user_id) not in ROLES_HABILITES:
        audit(conn, user_id, "decision_refusee_permission", f"alerte:{alerte_id}")
        conn.commit()
        raise PermissionRefusee(f"{user_id} n'est pas habilité")
    row = conn.execute("SELECT statut FROM alerte WHERE id=?", (alerte_id,)).fetchone()
    if row is None:
        raise KeyError(alerte_id)
    if row["statut"] != "a_qualifier":
        raise TransitionInvalide(f"alerte {alerte_id} déjà {row['statut']}")
    conn.execute(
        "UPDATE alerte SET statut=?, decide_par=?, decide_le=?, commentaire=? WHERE id=?",
        (decision, user_id, utc_now(), commentaire, alerte_id),
    )
    audit(conn, user_id, f"alerte_{decision}", f"alerte:{alerte_id}")
    conn.commit()


def ouvrir_intervention(conn: sqlite3.Connection, alerte_id: int, user_id: str) -> int:
    a = conn.execute("SELECT statut, equipement_id FROM alerte WHERE id=?", (alerte_id,)).fetchone()
    if a is None or a["statut"] != "validee":
        raise TransitionInvalide("intervention possible uniquement sur alerte validée")
    if _role(conn, user_id) not in ROLES_HABILITES:
        raise PermissionRefusee(user_id)
    cur = conn.execute(
        "INSERT INTO intervention(alerte_id, equipement_id, responsable_id, cree_le) VALUES (?,?,?,?)",
        (alerte_id, a["equipement_id"], user_id, utc_now()),
    )
    audit(conn, user_id, "intervention_ouverte", f"intervention:{cur.lastrowid}")
    conn.commit()
    return cur.lastrowid
