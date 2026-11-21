"""Ingestion CSV avec validation de contrat, déduplication, quarantaine, manifest et idempotence.

Flux F1 (Bibliothèque §5.3) : fichier disponible -> lot accepté ou rejet documenté.
Contrat de données : docs/data_contract.md.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .db import audit, utc_now

log = logging.getLogger("rcs.ingestion")

SOURCE_AI4I = {
    "id": "S04",
    "nom": "AI4I 2020 Predictive Maintenance Dataset (UCI)",
    "url": "https://archive.ics.uci.edu/dataset/601/ai4i",
    "licence": "CC BY 4.0",
    "categorie": "Substitut générique NON médical (données synthétiques industrielles)",
    "date_verif": "2026-11-20",
}

# Contrat : colonne source -> (colonne cible, type, min, max)
CONTRACT = {
    "UDI": ("cle_source", int, 1, None),
    "Type": ("type", str, None, None),
    "Air temperature [K]": ("air_temp_k", float, 250.0, 350.0),
    "Process temperature [K]": ("process_temp_k", float, 250.0, 380.0),
    "Rotational speed [rpm]": ("rpm", float, 0.0, 5000.0),
    "Torque [Nm]": ("torque_nm", float, 0.0, 200.0),
    "Tool wear [min]": ("tool_wear_min", float, 0.0, 400.0),
    "Machine failure": ("label", int, 0, 1),
}
ALLOWED_TYPES = {"L", "M", "H"}


@dataclass
class ImportReport:
    fichier: str
    sha256: str
    statut: str  # 'importe' | 'deja_importe' | 'rejete'
    lot_id: int | None = None
    nb_lignes: int = 0
    nb_acceptees: int = 0
    nb_rejetees: int = 0
    nb_doublons: int = 0
    erreurs: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_row(row: dict, line_no: int) -> tuple[dict | None, str | None]:
    out: dict = {}
    for src, (dst, typ, lo, hi) in CONTRACT.items():
        raw = row.get(src)
        if raw is None or str(raw).strip() == "":
            return None, f"ligne {line_no}: champ manquant '{src}'"
        try:
            val = typ(str(raw).strip())
        except ValueError:
            return None, f"ligne {line_no}: type invalide pour '{src}' ({raw!r})"
        if lo is not None and val < lo or hi is not None and val > hi:
            return None, f"ligne {line_no}: valeur hors plage pour '{src}' ({val})"
        out[dst] = val
    if out["type"] not in ALLOWED_TYPES:
        return None, f"ligne {line_no}: Type inconnu {out['type']!r}"
    if out["process_temp_k"] < out["air_temp_k"]:
        return None, f"ligne {line_no}: incohérence process_temp < air_temp"
    return out, None


def _ensure_reference_rows(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO source_donnees VALUES (:id,:nom,:url,:licence,:categorie,:date_verif)",
        SOURCE_AI4I,
    )
    for t, crit in (("L", "faible"), ("M", "moyenne"), ("H", "haute")):
        conn.execute(
            "INSERT OR IGNORE INTO equipement(id, type, modele, site, criticite, est_fictif) "
            "VALUES (?,?,?,?,?,1)",
            (f"AI4I-{t}", f"substitut fraiseuse qualité {t}", "AI4I synthétique", "simulé", crit),
        )


def import_csv(conn: sqlite3.Connection, path: str | Path, quarantine_dir: str | Path | None = None,
               acteur: str = "pipeline") -> ImportReport:
    path = Path(path)
    digest = sha256_file(path)
    _ensure_reference_rows(conn)

    existing = conn.execute("SELECT id FROM lot_import WHERE sha256 = ?", (digest,)).fetchone()
    if existing:
        log.info("Fichier déjà importé (lot %s) : aucune écriture", existing["id"])
        audit(conn, acteur, "import_ignore_idempotent", path.name)
        conn.commit()
        return ImportReport(path.name, digest, "deja_importe", lot_id=existing["id"])

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = set(CONTRACT) - set(reader.fieldnames or [])
        if missing:
            rep = ImportReport(path.name, digest, "rejete",
                               erreurs=[{"ligne": 0, "erreur": f"colonnes manquantes {sorted(missing)}"}])
            audit(conn, acteur, "import_rejete_schema", path.name)
            conn.commit()
            return rep
        rows = list(reader)

    accepted, rejected, seen = [], [], set()
    dup = 0
    for i, row in enumerate(rows, start=2):
        rec, err = validate_row(row, i)
        if err:
            rejected.append({"ligne": i, "erreur": err, "brut": row})
            continue
        key = (rec["type"], rec["cle_source"])
        if key in seen:
            dup += 1
            continue
        seen.add(key)
        accepted.append(rec)

    cur = conn.execute(
        "INSERT INTO lot_import(source_id, fichier, sha256, nb_lignes, nb_acceptees, nb_rejetees, nb_doublons, importe_le)"
        " VALUES (?,?,?,?,?,?,?,?)",
        ("S04", path.name, digest, len(rows), 0, len(rejected), dup, utc_now()),
    )
    lot_id = cur.lastrowid
    inserted = 0
    for rec in accepted:
        c = conn.execute(
            "INSERT OR IGNORE INTO observation(equipement_id, lot_id, cle_source, air_temp_k, process_temp_k, rpm,"
            " torque_nm, tool_wear_min, label, label_origine) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (f"AI4I-{rec['type']}", lot_id, str(rec["cle_source"]), rec["air_temp_k"], rec["process_temp_k"],
             rec["rpm"], rec["torque_nm"], rec["tool_wear_min"], rec["label"], "synthétique (AI4I)"),
        )
        if c.rowcount == 1:
            inserted += 1
        else:
            dup += 1  # déjà présent depuis un lot antérieur
    conn.execute("UPDATE lot_import SET nb_acceptees=?, nb_doublons=? WHERE id=?", (inserted, dup, lot_id))
    audit(conn, acteur, "import_lot", f"lot:{lot_id}")
    conn.commit()

    if quarantine_dir and rejected:
        q = Path(quarantine_dir)
        q.mkdir(parents=True, exist_ok=True)
        (q / f"{path.stem}_{digest[:8]}_rejets.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rejected), encoding="utf-8")

    log.info("Lot %s : %s acceptées, %s rejetées, %s doublons", lot_id, inserted, len(rejected), dup)
    return ImportReport(path.name, digest, "importe", lot_id, len(rows), inserted, len(rejected), dup,
                        [{"ligne": r["ligne"], "erreur": r["erreur"]} for r in rejected[:50]])


def write_manifest(report: ImportReport, out: str | Path) -> None:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"source": SOURCE_AI4I, "import": report.to_dict(), "genere_le": utc_now()}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
