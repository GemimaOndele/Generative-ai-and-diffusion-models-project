"""RCS-81 — auditeur reproductible du protocole commun TP04/TP05.

Ne contacte aucun modèle ni API, ne fabrique aucun résultat et ne fige pas
les jeux de test à la place de l'équipe. Évalue des exécutions réellement
tracées et approuvées, une fois disponibles.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import math
from pathlib import Path

CASE_COLUMNS = {"case_id", "category", "expected_behavior", "approval_state", "freeze_commit"}
RUN_COLUMNS = {
    "case_id", "strategy", "model_id", "model_version",
    "execution_mode", "success", "review_evidence",
    "latency_ms", "cost_eur", "citation_status", "route_reason",
}
IDS = [f"T{i:02d}" for i in range(1, 11)]
CATEGORIES = {
    "usual": 4,
    "complex": 2,
    "stress_source_absente": 1,
    "stress_source_contradictoire": 1,
    "stress_injection_indirecte": 1,
    "stress_donnee_sensible": 1,
}
STRATEGIES = ("mono-A", "mono-B", "V2")
CITATIONS = {"verified", "incorrect", "not_applicable", "unreviewed"}


def csv_rows(path: str | Path, columns: set[str]) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not columns.issubset(set(reader.fieldnames)):
            raise ValueError("Colonnes CSV absentes: " + ", ".join(sorted(columns - set(reader.fieldnames or []))))
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError("CSV mal formé: colonnes superflues dans une ligne")
    return rows


def positive_decimal(value: str, label: str) -> Decimal | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        parsed = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(label + " est non numérique") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(label + " doit être fini et >= 0")
    return parsed


def nearest_rank_p95(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(Decimal("0.95") * len(ordered)) - 1]


def decimal_str(value: Decimal | None, digits="0.000001") -> str | None:
    return None if value is None else str(value.quantize(Decimal(digits),rounding=ROUND_HALF_UP))


def check_manifest(rows: list[dict[str, str]]) -> tuple[bool, list[str]]:
    if len(rows) != 10:
        raise ValueError("Le jeu TP04/TP05 doit contenir exactement dix cas")
    ids=[row["case_id"].strip() for row in rows]
    if sorted(ids) != sorted(IDS):
        raise ValueError("Cas T01 à T10 exactement requis, sans doublons")
    for category,n in CATEGORIES.items():
        if sum(row["category"].strip() == category for row in rows) != n:
            raise ValueError("Distribution des six catégories de cas non conforme")
    blocked=[]
    for row in rows:
        if row["approval_state"].strip() != "frozen":
            blocked.append(f"{row['case_id']}: non gelé")
        if not row["freeze_commit"].strip():
            blocked.append(f"{row['case_id']}: référence de gel absente")
        if not row["expected_behavior"].strip():
            blocked.append(f"{row['case_id']}: comportement attendu manquant")
    hashes={r["freeze_commit"].strip() for r in rows}
    if len(hashes)>1:
        blocked.append("Références de gel différentes : vérifier la version du jeu")
    return not blocked, blocked


def summarize(manifest: str | Path, results: str | Path) -> dict:
    cases=csv_rows(manifest, CASE_COLUMNS)
    valid,blocked=check_manifest(cases)
    if not valid:
        return {
            "decision":"BLOCKED",
            "reason":"cases_not_frozen",
            "cases_count":len(cases),
            "blockers":blocked,
            "results":None,
            "go_no_go":"A TESTER",
        }
    runs=csv_rows(results, RUN_COLUMNS)
    if not runs:
        return {"decision":"BLOCKED","reason":"no_executed_results",
                "blockers":["Aucune exécution de modèle enregistrée."],
                "results":None,"go_no_go":"A TESTER"}
    if len(runs)!=30:
        raise ValueError("Il faut 10 lignes par stratégie mono-A/mono-B/V2 pour la comparaison")
    grouped={name:[] for name in STRATEGIES}
    seen=set()
    for r in runs:
        strategy=r["strategy"].strip()
        case=r["case_id"].strip()
        if strategy not in grouped or case not in IDS:
            raise ValueError("Stratégie ou case_id non reconnu")
        key=(strategy,case)
        if key in seen:
            raise ValueError("Doublon stratégie/cas")
        seen.add(key)
        if r["execution_mode"].strip()!="live":
            raise ValueError("Un mock ne constitue pas une évaluation LLM réelle")
        if not all((r[x] or "").strip() for x in ("model_id","model_version","review_evidence")):
            raise ValueError("Exécution sans modèle/version ou preuve de revue humaine")
        if r["success"].strip() not in {"pass","fail"}:
            raise ValueError("Succès métier doit être jugé pass/fail, selon cas gelé")
        if r["citation_status"].strip() not in CITATIONS:
            raise ValueError("Statut de citation incorrect")
        if strategy=="V2" and not r["route_reason"].strip():
            raise ValueError("La V2 doit journaliser la raison du routage")
        latency=positive_decimal(r["latency_ms"],"latency_ms")
        cost=positive_decimal(r["cost_eur"],"cost_eur")
        if latency is None:
            raise ValueError("Latence de chaque exécution live nécessaire")
        grouped[strategy].append({**r,"latency_numeric":latency,"cost_numeric":cost})
    for key,rr in grouped.items():
        if {r["case_id"].strip() for r in rr} != set(IDS):
            raise ValueError("Stratégie sans les dix mêmes cas")
    a={r["model_id"] for r in grouped["mono-A"]}
    b={r["model_id"] for r in grouped["mono-B"]}
    if len(a)!=1 or len(b)!=1 or a==b:
        raise ValueError("Deux modèles LLM distincts A/B doivent être identifiés")
    metrics={}
    for strategy,rr in grouped.items():
        successes=sum(r["success"]=="pass" for r in rr)
        costs=[r["cost_numeric"] for r in rr]
        complete_costs=all(c is not None for c in costs)
        total=sum(costs,Decimal(0)) if complete_costs else None
        metrics[strategy]={
            "model_ids": sorted({r["model_id"] for r in rr}),
            "cases":len(rr),
            "business_success_count":successes,
            "business_success_rate":decimal_str(Decimal(successes)/Decimal(10),"0.000"),
            "p95_latency_ms":decimal_str(nearest_rank_p95([r["latency_numeric"] for r in rr]),"0.001"),
            "cost_total_eur":decimal_str(total),
            "cost_per_success_eur":decimal_str(total / successes) if successes and total is not None else None,
            "citation_verified_count":sum(r["citation_status"]=="verified" for r in rr),
            "citation_unreviewed_count":sum(r["citation_status"]=="unreviewed" for r in rr),
            "cost_coverage":str(sum(c is not None for c in costs))+"/10",
            "remote_energy_kwh":None,
            "remote_co2e_kg":None,
            "remote_energy_status":"ND",
        }
    return {
        "decision":"COMPARISON_CALCULATED_NOT_APPROVED",
        "go_no_go":"REVUE HUMAINE REQUISE",
        "workload_cases":len(IDS),
        "workload_version":cases[0]["freeze_commit"],
        "unit_of_analysis":"demande documentaire correctement traitée, citation ou abstention selon attendu gelé",
        "results":metrics,
        "notes":[
            "La présence d'un fichier prétendument live ne prouve pas sa provenance : relecture des traces obligatoire.",
            "Cost euro calculé seulement lorsque les dix coûts sont disponibles ; zéro succès -> coût unitaire ND.",
            "Les valeurs d'énergie API distante restent ND, aucune conversion depuis les tokens/tarifs.",
            "Aucune décision biomédicale autonome, aucune certification réglementaire.",
        ],
    }


def main() -> None:
    parser=argparse.ArgumentParser(description="RCS-81 : comparatif mono-A / mono-B / V2")
    parser.add_argument("--manifest",default="planning/rcs81_case_manifest.csv")
    parser.add_argument("--results",default="planning/rcs81_runs_template.csv")
    args=parser.parse_args()
    print(json.dumps(summarize(args.manifest,args.results),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
