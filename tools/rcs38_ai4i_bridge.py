"""RCS-38 ↔ RCS-49/50/52: READ-ONLY preview of the AI4I industrial proxy.

The output is deliberately NOT a RCS-38 fictional_demo_only fixture: it must
never be posted to /api/v1/demo/overview or used by the simulated decision API.
No patient data, labels, actions, or machine-control instructions are exported.
This adapter assumes Omar's RCS-50 schema; it does not modify his modules.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3

SOURCE_MODE = "industrial_proxy_non_medical"
MAX_ROWS = 1000


def preview_ai4i(db_path: str | Path, limit: int = 100) -> dict:
    """Read a versioned AI4I SQLite POC, preserving provenance and uncertainty.

    Raises ValueError when the source is not explicitly tagged as non-medical
    industrial synthetic data. The source DB is opened in SQLite read-only mode.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_ROWS:
        raise ValueError(f"limit must be an integer from 1 to {MAX_ROWS}")
    path = Path(db_path).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError("SQLite file required")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        src = connection.execute(
            "SELECT id, nom, url, licence, categorie, date_verif "
            "FROM source_donnees WHERE id = ?", ("S04",)
        ).fetchone()
        if src is None or not (
            "non médical" in src["categorie"].casefold()
            or "non-medical" in src["categorie"].casefold()
        ):
            raise ValueError("Only explicitly non-medical S04 AI4I source accepted")
        devices = connection.execute(
            "SELECT id, type, site, criticite FROM equipement "
            "WHERE est_fictif = 1 AND id LIKE 'AI4I-%' ORDER BY id"
        ).fetchall()
        if not devices:
            raise ValueError("No explicitly synthetic AI4I equipment found")
        rows = connection.execute(
            """SELECT o.id, o.equipement_id, o.cle_source, o.air_temp_k,
                      o.process_temp_k, o.rpm, o.torque_nm, o.tool_wear_min,
                      l.fichier, l.sha256, l.importe_le,
                      a.score, a.seuil, a.model_version
               FROM observation o
               JOIN lot_import l ON l.id = o.lot_id
               LEFT JOIN analyse_modele a ON a.id = (
                   SELECT max(a2.id) FROM analyse_modele a2
                   WHERE a2.observation_id = o.id
               )
               WHERE l.source_id = ? AND o.equipement_id LIKE 'AI4I-%'
               ORDER BY o.id ASC LIMIT ?""", ("S04", limit)
        ).fetchall()
        device_ids = {d["id"] for d in devices}
        observations = []
        for row in rows:
            if row["equipement_id"] not in device_ids:
                raise ValueError("Observation references non-synthetic equipment")
            observations.append({
                "equipment_id": row["equipement_id"],
                "source_record_id": row["cle_source"],  # AI4I UDI, NOT a real device UDI
                "measurement": {
                    "air_temp_k": row["air_temp_k"],
                    "process_temp_k": row["process_temp_k"],
                    "rpm": row["rpm"],
                    "torque_nm": row["torque_nm"],
                    "tool_wear_min": row["tool_wear_min"],
                },
                "anomaly": {
                    "score": row["score"], "threshold": row["seuil"],
                    "model_version": row["model_version"],
                    "flag": bool(row["score"] >= row["seuil"])
                    if row["score"] is not None and row["seuil"] is not None else None,
                },
                "provenance": {
                    "source_id": "S04",
                    "file_name": row["fichier"],
                    "file_sha256": row["sha256"],
                    "imported_utc": row["importe_le"],
                },
            })
        return {
            "schema_version": "rcs38-ai4i-readonly-v0.1",
            "source_mode": SOURCE_MODE,
            "read_only": True,
            "medical_data": False,
            "clinical_use": False,
            "control_enabled": False,
            "site_is_fictional": True,
            "x_axis": "source_record_id_not_time",
            "source": {k: src[k] for k in src.keys()},
            "equipment": [
                {"id": d["id"], "category": "industrial_proxy", "type": d["type"],
                 "site": d["site"], "criticality": d["criticite"]}
                for d in devices
            ],
            "observations": observations,
            "actions": [],  # Never map imported anomalies into actionable decisions.
            "limitation": "AI4I is industrial synthetic data, not medical telemetry; "
                          "the source record key is not time and no clinical "
                          "performance or maintenance action is inferred.",
        }
    finally:
        connection.close()

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Export de consultation AI4I non médical (aucune écriture DB)"
    )
    parser.add_argument("--db", type=Path, required=True,
                        help="Base SQLite créée par le pipeline RCS-50")
    parser.add_argument("--out", type=Path, required=True,
                        help="Fichier JSON local destiné à ai4i_preview.html")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.db.expanduser().resolve() == args.out.expanduser().resolve():
        parser.error("--out must differ from --db")
    exported = preview_ai4i(args.db, args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(exported, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Export non médical en lecture seule : {len(exported['observations'])} observations.")
