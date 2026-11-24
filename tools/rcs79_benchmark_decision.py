"""RCS-79 — synthèse benchmark V2 et décision GO/NO-GO traçable.

Aucune mesure n'est produite ici : les résultats, les seuils approuvés, les
modèles autorisés, le relecteur et le commit doivent être fournis
explicitement. Sans gel RCS-81 ni modèles validés la décision est NO_GO ;
avec gel et modèles mais sans exécution réelle elle reste A_TESTER.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.rcs81_evaluate import CASE_COLUMNS, check_manifest, csv_rows

ND = "ND"
ISSUE = "RCS-79"
DEFAULT_MANIFEST = Path("planning") / "rcs81_case_manifest.csv"
ACCEPTANCE_REL = Path("governance") / "rcs79" / "decision.json"
DOC_REL = Path("docs") / "48_rcs79_benchmark_decision.md"
STRATEGIES = ("mono-A", "mono-B", "V2")
REQUIRED_METRICS = ("quality", "p95_ms", "cost_eur", "co2e_kg", "energy_status")
MODEL_FIELDS = ("model_name", "provider", "version", "license", "region", "retention_policy")


def _load_json(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if path is None:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} doit contenir un objet JSON")
    return payload


def _number(value: Any) -> Optional[float]:
    if value in (None, "", ND):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def models_valid(payload: Optional[Dict[str, Any]]) -> bool:
    if not payload or not all(key in payload for key in ("A", "B")):
        return False
    specs = [payload["A"], payload["B"]]
    if not all(isinstance(spec, dict) for spec in specs):
        return False
    for spec in specs:
        if not all(str(spec.get(field, "")).strip() for field in MODEL_FIELDS):
            return False
        if spec.get("validated") is not True or spec.get("usage_rights_verified") is not True:
            return False
        if spec.get("data_transfer_authorized") is not True:
            return False
    identities = {
        (str(spec["provider"]).lower(), str(spec["model_name"]).lower(), str(spec["version"]).lower())
        for spec in specs
    }
    return len(identities) == 2


def results_valid(payload: Optional[Dict[str, Any]]) -> bool:
    if not payload or payload.get("execution_mode") != "live":
        return False
    if payload.get("cases_count") != 10:
        return False
    strategies = payload.get("strategies")
    if not isinstance(strategies, dict) or not all(key in strategies for key in STRATEGIES):
        return False
    for name in STRATEGIES:
        item = strategies[name]
        if not isinstance(item, dict):
            return False
        if any(_number(item.get(key)) is None for key in ("quality", "p95_ms", "cost_eur", "co2e_kg")):
            return False
        if item.get("energy_status") in (None, "", ND):
            return False
    thresholds = payload.get("approved_thresholds")
    if not isinstance(thresholds, dict):
        return False
    return all(
        _number(thresholds.get(key)) is not None
        for key in ("quality_delta", "p95_ms", "cost_eur")
    )


def build_report(
    root: Path,
    manifest: Optional[str] = None,
    results: Optional[str] = None,
    models: Optional[str] = None,
    reviewer: Optional[str] = None,
    commit: Optional[str] = None,
) -> Dict[str, Any]:
    manifest_path = Path(manifest) if manifest else root / DEFAULT_MANIFEST
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    try:
        rows = csv_rows(manifest_path, CASE_COLUMNS)
        cases_frozen, case_blockers = check_manifest(rows)
    except (OSError, ValueError):
        cases_frozen, case_blockers = False, ["Manifeste RCS-81 absent ou invalide"]

    models_payload = _load_json(models)
    results_payload = _load_json(results)
    reviewer = reviewer or ND
    commit = commit or ND

    comparatif: Dict[str, Dict[str, Any]] = {}
    for name in STRATEGIES:
        if results_valid(results_payload):
            item = results_payload["strategies"][name]
            comparatif[name] = {key: item.get(key) for key in REQUIRED_METRICS}
        else:
            comparatif[name] = {key: ND for key in REQUIRED_METRICS}

    gates: Dict[str, bool] = {
        "cas_geles": cases_frozen,
        "modeles_ab_valides": models_valid(models_payload),
        "resultats_live_reels": results_valid(results_payload),
        "qualite_v2_superieure": False,
        "latence_conforme": False,
        "cout_conforme": False,
        "energie_documentee": False,
        "revue_humaine": reviewer != ND,
        "commit_reference": bool(re.fullmatch(r"[0-9a-f]{7,64}", commit.strip().lower())),
    }
    if results_valid(results_payload):
        thresholds = results_payload["approved_thresholds"]
        v2 = results_payload["strategies"]["V2"]
        monos = [results_payload["strategies"][name]["quality"] for name in ("mono-A", "mono-B")]
        gates["qualite_v2_superieure"] = (
            float(v2["quality"]) - max(float(value) for value in monos)
            >= float(thresholds["quality_delta"])
        )
        gates["latence_conforme"] = float(v2["p95_ms"]) <= float(thresholds["p95_ms"])
        gates["cout_conforme"] = float(v2["cost_eur"]) <= float(thresholds["cost_eur"])
        gates["energie_documentee"] = all(
            results_payload["strategies"][name]["energy_status"] in {"mesuré", "calculé", "estimé"}
            for name in STRATEGIES
        )

    if not (gates["cas_geles"] and gates["modeles_ab_valides"]):
        decision = "NO_GO"
    elif all(gates.values()):
        decision = "GO"
    else:
        decision = "A_TESTER"

    blocking_reasons: List[str] = []
    if not gates["cas_geles"]:
        blocking_reasons.append("Cas RCS-81 non gelés collectivement : freeze_commit absent ou invalide.")
    if not gates["modeles_ab_valides"]:
        blocking_reasons.append("Modèles A/B réels non validés (identité, licence, droits, région, rétention).")
    if not gates["resultats_live_reels"]:
        blocking_reasons.append("Aucune exécution live réelle sur dix cas : le mode démo ne mesure pas la qualité.")
    for key, reason in (
        ("qualite_v2_superieure", "Gain V2 inférieur au seuil approuvé ou seuil ND."),
        ("latence_conforme", "p95 V2 supérieure au seuil approuvé ou seuil ND."),
        ("cout_conforme", "Coût V2 supérieur au seuil approuvé ou seuil ND."),
        ("energie_documentee", "Énergie/CO₂e non documentée ou non calculée sur un périmètre commun."),
        ("revue_humaine", "Relecteur humain absent."),
        ("commit_reference", "Commit de référence absent."),
    ):
        if not gates[key]:
            blocking_reasons.append(reason)
    if case_blockers and not gates["cas_geles"]:
        blocking_reasons.extend(case_blockers[:2])

    return {
        "schema": "rcs79_benchmark_decision/v1",
        "issue": ISSUE,
        "inputs": {
            "manifest": manifest_path.as_posix(),
            "results": results or ND,
            "models": models or ND,
        },
        "comparatif": comparatif,
        "gates": gates,
        "decision": decision,
        "reviewer": reviewer,
        "commit": commit,
        "blocking_reasons": blocking_reasons,
        "liens": [
            "docs/05_tp04_benchmark.md",
            "data/manifest.md",
            "planning/rcs81_case_manifest.csv",
            "README.md",
        ],
        "note": "Un mock ou le mode démo ne peut jamais étayer un GO.",
    }


def serialize(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_doc(report: Dict[str, Any]) -> str:
    lines = [
        f"# {ISSUE} — Benchmark V2 Multi-LLM et décision GO/NO-GO",
        "",
        "> Ce document est généré à partir des preuves fournies. Sans gel RCS-81 "
        "ni modèles A/B validés, la décision est **NO_GO** ; sans exécution live, "
        "elle reste **A_TESTER**. Aucune valeur n'est simulée ici.",
        "",
        "## Comparatif mono / V2",
        "",
        "| Stratégie | Qualité | p95 (ms) | Coût (€) | CO₂e (kg) | Statut énergie |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name in STRATEGIES:
        item = report["comparatif"][name]
        lines.append(
            f"| {name} | {item['quality']} | {item['p95_ms']} | {item['cost_eur']} | "
            f"{item['co2e_kg']} | {item['energy_status']} |"
        )
    lines += [
        "",
        "## Portes de décision",
        "",
        "| Contrôle | Résultat |",
        "|---|---|",
    ]
    for key, value in report["gates"].items():
        lines.append(f"| {key} | {'OK' if value else 'BLOQUÉ'} |")
    lines += [
        "",
        f"**Décision : {report['decision']}** — relecteur : {report['reviewer']} — "
        f"commit : {report['commit']}.",
        "",
        "## Limites et bloquants",
        "",
    ]
    lines += [f"- {reason}" for reason in report["blocking_reasons"]]
    lines += [
        f"- {report['note']}",
        "",
        "## Preuves et reproduction",
        "",
    ]
    lines += [f"- `{link}`" for link in report["liens"]]
    lines += [
        "",
        "```bash",
        "python -m tools.rcs79_benchmark_decision --write",
        "python -m tools.rcs79_benchmark_decision --manifest <manifeste_gelé.csv> "
        "--models <modeles.json> --results <resultats_live.json> "
        "--reviewer <nom> --commit <sha> --write",
        "python -m tools.rcs79_benchmark_decision --check",
        "python -m unittest tests.test_rcs79_benchmark_decision -v",
        "```",
        "",
        "Le rapport complète `docs/05_tp04_benchmark.md` et le protocole RCS-81, "
        "sans remplacer la revue humaine ni le gel collectif des cas.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(root: Path, report: Dict[str, Any]) -> None:
    for rel, content in (
        (ACCEPTANCE_REL, serialize(report)),
        (DOC_REL, render_doc(report)),
    ):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_outputs(root: Path, report: Dict[str, Any]) -> tuple[bool, List[str]]:
    reasons: List[str] = []
    for rel, content in (
        (ACCEPTANCE_REL, serialize(report)),
        (DOC_REL, render_doc(report)),
    ):
        path = root / rel
        if not path.is_file():
            reasons.append(f"{rel.as_posix()} absent")
        elif path.read_text(encoding="utf-8") != content:
            reasons.append(f"{rel.as_posix()} obsolète : relancer --write")
    if report["decision"] == "GO" and not all(report["gates"].values()):
        reasons.append("GO sans toutes les portes validées")
    if report["decision"] == "GO" and report["reviewer"] == ND:
        reasons.append("GO sans revue humaine")
    if report["decision"] not in {"GO", "NO_GO", "A_TESTER"}:
        reasons.append("décision inconnue")
    return not reasons, reasons


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RCS-79 — décision benchmark V2")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest")
    parser.add_argument("--results")
    parser.add_argument("--models")
    parser.add_argument("--reviewer")
    parser.add_argument("--commit")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            args.root, args.manifest, args.results, args.models, args.reviewer, args.commit
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1
    if args.write:
        write_outputs(args.root, report)
    if args.check:
        ok, reasons = check_outputs(args.root, report)
        if not ok:
            print("\n".join(reasons))
            return 1
    print(serialize(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
