"""Audit des cas candidats C3 / diffusion, sans gel ou manipulation de résultats."""
from __future__ import annotations
import csv
import json
import argparse
from pathlib import Path

REQUIRED = {"case_id", "category", "input_ref", "dataset_id", "label_source",
            "expected_behavior", "check_mode", "status"}
STATUSES = {"proposed", "ready_for_review", "frozen"}


def inspect_cases(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not REQUIRED.issubset(set(reader.fieldnames or [])):
            raise ValueError("Colonnes manquantes au contrat des cas C3")
        rows = list(reader)
    if not 8 <= len(rows) <= 10:
        raise ValueError("C3 : le protocole propose 8 à 10 cas à figer")
    ids = [row["case_id"].strip() for row in rows]
    if len(set(ids)) != len(ids) or any(not i for i in ids):
        raise ValueError("Les identifiants de cas doivent être uniques et non vides")
    missing = []
    for row in rows:
        status = row["status"].strip()
        if status not in STATUSES:
            raise ValueError("status doit être proposed, ready_for_review ou frozen")
        absent = [f for f in ("input_ref", "dataset_id", "label_source", "expected_behavior", "check_mode")
                  if not (row.get(f) or "").strip()]
        if absent:
            missing.append({"case_id": row["case_id"], "missing": absent})
        if status == "frozen" and absent:
            raise ValueError("Interdiction de geler un cas avec provenance/attendu incomplet")
    return {
        "case_count": len(rows),
        "frozen_count": sum(r["status"].strip() == "frozen" for r in rows),
        "can_request_collective_freeze": not missing and all(
            r["status"] in {"ready_for_review", "frozen"} for r in rows),
        "automatically_frozen": False,
        "missing_source_or_expected": missing,
        "scientific_results_measured": False,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="RCS-69 : audit des cas expérimentaux C3")
    p.add_argument("--cases", default="planning/rcs69_cases_proposed.csv")
    a = p.parse_args()
    print(json.dumps(inspect_cases(a.cases), ensure_ascii=False, indent=2))
