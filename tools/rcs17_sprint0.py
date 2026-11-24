"""Préparation du Sprint 0 — validation de capacité, sans démarrer Jira (RCS-17).

La feuille vierge ne doit jamais être interprétée comme un accord de l'équipe.
Les disponibilités individuelles sont potentiellement privées : publier uniquement
une synthèse agrégée approuvée dans le dépôt public.
"""
from __future__ import annotations
import argparse
import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

EXPECTED = {"Gémima", "Aminata", "Omar", "Elias", "Ayoub"}
FIELDS = {"member", "available_hours", "approved", "evidence_ref"}


def assess_capacity(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not FIELDS.issubset(set(reader.fieldnames or [])):
            raise ValueError("Champs manquants : " + ", ".join(sorted(FIELDS - set(reader.fieldnames or []))))
        rows = list(reader)
    seen = set()
    blockers = []
    approved = 0
    recorded = 0
    total = Decimal("0")
    for row in rows:
        member = (row.get("member") or "").strip()
        if member not in EXPECTED:
            raise ValueError("Membre non reconnu ; vérifier la fiche d'équipe et le CSV")
        if member in seen:
            raise ValueError("Ligne membre dupliquée")
        seen.add(member)
        status = (row.get("approved") or "").strip().lower()
        if status not in {"yes", "no", "pending"}:
            raise ValueError("approved doit valoir yes, no ou pending")
        raw = (row.get("available_hours") or "").strip()
        if raw:
            try:
                hours = Decimal(raw)
            except InvalidOperation as exc:
                raise ValueError("Capacité non numérique") from exc
            if not hours.is_finite() or hours < 0:
                raise ValueError("Capacité doit être finie et positive ou nulle")
            total += hours
            recorded += 1
        if status == "yes" and not raw:
            raise ValueError("Ne pas approuver une capacité sans nombre d'heures")
        if status == "yes" and not (row.get("evidence_ref") or "").strip():
            raise ValueError("Toute approbation doit citer une confirmation")
        if status == "yes":
            approved += 1
        else:
            blockers.append(member + " : capacité/approbation en attente")
        if not raw:
            blockers.append(member + " : nombre d'heures non renseigné")
    for missing in sorted(EXPECTED - seen):
        blockers.append(missing + " : ligne absente")

    ready = len(seen) == 5 and approved == 5 and not blockers
    return {
        "sprint": "Sprint 0",
        "status": "capacities_confirmed" if ready else "blocked_pending_team_decision",
        "ready_for_manual_planning": ready,
        "ready_to_start_automatically": False,
        "approved_count": approved,
        "member_count": len(seen),
        "recorded_capacity_hours": str(total) if recorded else None,
        "coverage": str(recorded) + "/5",
        "blockers": blockers,
        "next_step": "Estimer les tickets et voter les dates/engagements ; ne jamais démarrer Jira automatiquement.",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="RCS-17 : contrôle de préparation avant Sprint 0")
    p.add_argument("--capacity", default="planning/rcs17_capacity.csv")
    args = p.parse_args()
    print(json.dumps(assess_capacity(args.capacity), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
