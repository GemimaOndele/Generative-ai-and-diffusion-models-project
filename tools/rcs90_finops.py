"""RoboCare Sentinel — calculateur FinOps transparent (RCS-90).

Ne contient aucun montant, taux horaire ni résultat d'expérience réel.
Sépare débours, prévisions, heures de travail et valorisation *hypothétique*.
Dépendances : bibliothèque standard Python uniquement.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path

COST_REQUIRED = {
    "entry_id", "jira_ticket", "category", "cost_class", "status",
    "amount_eur", "currency", "included_in_api", "source_ref", "notes"
}
WORKLOG_REQUIRED = {
    "entry_id", "jira_ticket", "member", "activity", "status",
    "hours", "hypothetical_hourly_rate_eur", "rate_source", "notes"
}
STATUS = {"actual", "estimated"}
CATEGORIES = {"api", "cloud", "storage", "license", "monitoring", "equipment", "other"}
MONEY_CATEGORIES = {"fixed", "variable"}


def _read_csv(path: str | Path, required: set[str]) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames and len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("Colonnes CSV dupliquées")
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            missing = sorted(required - set(reader.fieldnames or []))
            raise ValueError("Colonnes CSV manquantes : " + ", ".join(missing))
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError("Trop de colonnes dans une ligne CSV")
    if any(any(value is None for value in row.values()) for row in rows):
        raise ValueError("Ligne CSV incomplète")
    keys = [r["entry_id"].strip() for r in rows]
    if any(not key for key in keys):
        raise ValueError("Chaque ligne doit avoir un entry_id non vide")
    if len(keys) != len(set(keys)):
        raise ValueError("entry_id dupliqué : risque de double comptage")
    return rows


def _decimal(raw: str, field: str, *, optional: bool = False) -> Decimal | None:
    value = str(raw or "").strip()
    if not value and optional:
        return None
    try:
        n = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} doit être un nombre décimal") from exc
    if not n.is_finite() or n < 0:
        raise ValueError(f"{field} doit être positif ou nul et fini")
    return n


def _rounded(n: Decimal | None) -> str | None:
    if n is None:
        return None
    return str(n.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def summarize(
    costs_path: str | Path,
    worklog_path: str | Path,
    *,
    successes: int | None = None,
    success_source: str | None = None,
) -> dict:
    """Résumé observé et borné, jamais un coût complet fictivement garanti.

    Coût par succès : uniquement à partir des décaissements réels *observés*,
    sur un périmètre cohérent. Si des postes manquent, ce n'est qu'une borne
    partielle — la décision d'utiliser l'indicateur appartient à l'équipe.
    """
    if successes is not None:
        if isinstance(successes, bool) or not isinstance(successes, int) or successes < 0:
            raise ValueError("Le nombre de succès doit être un entier positif ou nul")
        if not success_source or not success_source.strip():
            raise ValueError("Renseigner success_source (lien de preuve du benchmark)")
    costs = _read_csv(costs_path, COST_REQUIRED)
    worklogs = _read_csv(worklog_path, WORKLOG_REQUIRED)
    spent = Decimal("0")
    estimated = Decimal("0")
    actual_count = estimate_count = excluded_count = missing_count = 0
    actual_hours = Decimal("0")
    estimated_hours = Decimal("0")
    actual_hours_count = estimated_hours_count = 0
    priced_labor = Decimal("0")
    labor_priced_count = 0
    for row in costs:
        if not row["jira_ticket"].strip():
            raise ValueError("Une dépense doit être reliée à un ticket")
        status = row["status"].strip().lower()
        category = row["category"].strip().lower()
        cost_class = row["cost_class"].strip().lower()
        inc = row["included_in_api"].strip().lower()
        if status not in STATUS or category not in CATEGORIES or cost_class not in MONEY_CATEGORIES:
            raise ValueError(f"Valeurs status/category/cost_class invalides : {row['entry_id']}")
        if inc not in {"yes", "no"}:
            raise ValueError("included_in_api doit valoir yes ou no")
        if row["currency"].strip().upper() != "EUR":
            raise ValueError("Seules les écritures EUR sont acceptées : aucune conversion implicite")
        amount = _decimal(row["amount_eur"], "amount_eur", optional=True)
        if amount is None:
            missing_count += 1
            continue
        if status == "actual" and not row["source_ref"].strip():
            raise ValueError("Toute dépense réelle doit citer une facture / preuve")
        if inc == "yes":
            excluded_count += 1
            continue
        if status == "actual":
            spent += amount
            actual_count += 1
        else:
            estimated += amount
            estimate_count += 1
    for row in worklogs:
        status = row["status"].strip().lower()
        if status not in STATUS:
            raise ValueError(f"Statut worklog invalide : {row['entry_id']}")
        if not row["member"].strip() or not row["jira_ticket"].strip():
            raise ValueError("Une ligne de temps doit lier membre et ticket")
        hours = _decimal(row["hours"], "hours", optional=True)
        rate = _decimal(row["hypothetical_hourly_rate_eur"], "rate", optional=True)
        if rate is not None and not row["rate_source"].strip():
            raise ValueError("Tout taux horaire hypothétique doit avoir une source")
        if hours is None:
            continue
        if status == "actual":
            actual_hours += hours
            actual_hours_count += 1
            if rate is not None:
                priced_labor += hours * rate
                labor_priced_count += 1
        else:
            estimated_hours += hours
            estimated_hours_count += 1

    partial_unit_cost = None
    if successes is not None and successes > 0 and actual_count:
        partial_unit_cost = spent / Decimal(successes)
    return {
        "project": "RoboCare Sentinel",
        "report_scope": "décaissements observés, non nécessairement exhaustifs",
        "status": "preparatory" if not (costs or worklogs) else "partial_observations",
        "cash_actual_observed_eur": _rounded(spent) if actual_count else None,
        "cash_estimated_entries_eur": _rounded(estimated) if estimate_count else None,
        "work_hours_actual_reported": _rounded(actual_hours) if actual_hours_count else None,
        "work_hours_estimated": _rounded(estimated_hours) if estimated_hours_count else None,
        "labor_hypothetical_eur": _rounded(priced_labor) if labor_priced_count else None,
        "cost_per_success_observed_cash_eur": _rounded(partial_unit_cost),
        "successes_supplied": successes,
        "successes_source": success_source,
        "coverage": {
            "cost_entries": len(costs),
            "actual_cost_entries_counted": actual_count,
            "estimated_cost_entries_counted": estimate_count,
            "included_in_api_excluded": excluded_count,
            "unknown_amount_entries": missing_count,
            "worklog_entries": len(worklogs),
            "labor_entries_with_hypothetical_rate": labor_priced_count,
        },
        "warnings": [
            "Ne jamais additionner la valorisation hypothétique du travail aux dépenses réelles sans changer explicitement de convention.",
            "Le coût observé par succès peut être incomplet : vérifier périmètre de l'échantillon, allocations, coût fournisseur et succès.",
            "ND est représenté par null, et jamais par 0. Aucune performance scientifique n'est validée par ce programme.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="RCS-90 : synthèse FinOps à partir de CSV autorisés")
    parser.add_argument("--costs", default="planning/rcs90_costs.csv")
    parser.add_argument("--worklogs", default="planning/rcs90_worklogs.csv")
    parser.add_argument("--successes", type=int, default=None)
    parser.add_argument("--success-source", default=None)
    parser.add_argument("--output", help="Chemin JSON local, facultatif")
    args = parser.parse_args()
    result = summarize(args.costs, args.worklogs,
                       successes=args.successes, success_source=args.success_source)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
