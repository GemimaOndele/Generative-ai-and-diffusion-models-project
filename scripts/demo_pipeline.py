"""Démonstration de bout en bout (flux F1→F5) sur SQLite :
import AI4I (idempotent) -> scoring -> alertes dédupliquées -> décision technicien -> intervention -> audit.

    python scripts/demo_pipeline.py [--db data/rcs_poc.sqlite]

Le modèle de scoring utilisé ici est la baseline B0-a z-score « physics » (la plus performante au seuil
5 % FPR dans J1, cf. docs/07_j1_diffusion_resultats.md) ; le DDPM peut être branché de la même façon.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from rcs import DATA_RAW  # noqa: E402
from rcs import alerts as A  # noqa: E402
from rcs.db import connect  # noqa: E402
from rcs.ingestion import import_csv, write_manifest  # noqa: E402
from rcs.j1.baselines import ZScoreRule  # noqa: E402
from rcs.j1.data import load_ai4i, make_splits, numeric_features  # noqa: E402
from rcs.j1.evaluate import threshold_at_fpr  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "rcs_poc.sqlite"))
    ap.add_argument("--limit", type=int, default=200, help="nb d'observations scorées pour la démo")
    args = ap.parse_args()
    conn = connect(args.db)
    conn.execute("INSERT OR IGNORE INTO utilisateur VALUES ('tech-01','Technicien A','technicien')")

    src = DATA_RAW / "ai4i2020.csv"
    r1 = import_csv(conn, src, quarantine_dir=ROOT / "data" / "quarantine")
    r2 = import_csv(conn, src)  # 2e import identique : doit être ignoré
    write_manifest(r1 if r1.statut == "importe" else r2, ROOT / "data" / "manifests" / "ai4i_import.json")
    print(f"import 1 : {r1.statut} ({r1.nb_acceptees} acceptées) | import 2 : {r2.statut}")

    df = load_ai4i()
    sp = make_splits(df, "physics")
    model = ZScoreRule(sp.n_numeric)
    thr = threshold_at_fpr(model.score(sp.x_val), sp.y_val)
    x_num, _ = numeric_features(df, "physics")
    z = (x_num - sp.mean) / sp.std
    scores = model.score(z)

    rows = conn.execute("SELECT id, CAST(cle_source AS INTEGER) AS udi FROM observation ORDER BY id LIMIT ?",
                        (args.limit,)).fetchall()
    n_alert = 0
    for _ in range(2):  # rejouer le scoring deux fois : aucune alerte en double
        n_alert = 0
        for r in rows:
            _, alerte_id = A.enregistrer_analyse(conn, r["id"], "B0a_zscore_physics@v1",
                                                 float(scores[r["udi"] - 1]), thr)
            n_alert += alerte_id is not None
    total_alertes = conn.execute("SELECT COUNT(*) FROM alerte").fetchone()[0]
    print(f"seuil={thr:.3f} ; alertes sur {len(rows)} observations : {n_alert} (table alerte : {total_alertes})")

    first = conn.execute("SELECT id FROM alerte WHERE statut='a_qualifier' ORDER BY id LIMIT 2").fetchall()
    if first:
        A.decider_alerte(conn, first[0]["id"], "tech-01", "validee", "écart thermique confirmé (démo)")
        iid = A.ouvrir_intervention(conn, first[0]["id"], "tech-01")
        print(f"alerte {first[0]['id']} validée -> intervention {iid}")
    if len(first) > 1:
        A.decider_alerte(conn, first[1]["id"], "tech-01", "rejetee", "fausse alerte (démo)")
        print(f"alerte {first[1]['id']} rejetée")
    audit = [dict(r) for r in conn.execute("SELECT acteur, evenement, cible FROM audit ORDER BY id DESC LIMIT 6")]
    print("audit (6 derniers) :", json.dumps(audit, ensure_ascii=False))
    print("Rappel : aucune commande n'est envoyée à un équipement ; données AI4I synthétiques non médicales.")


if __name__ == "__main__":
    main()
