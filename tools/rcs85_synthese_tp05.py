"""RCS-85 — synthèse TP05 à partir des mesures réellement versées au dépôt.

Le fichier ``experiments/results/tp05_mesures.csv`` ne contient aujourd'hui que
son en-tête : toutes les valeurs de synthèse restent donc ``ND`` et la décision
reste **À TESTER**. Aucun coût, émission, risque ni statut n'est fabriqué.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

ND = "ND"
ISSUE = "RCS-85"
MEASURES_REL = Path("experiments") / "results" / "tp05_mesures.csv"
SOURCE_DOC_REL = Path("docs") / "06_tp05_finops_green_ethique.md"
ACCEPTANCE_REL = Path("governance") / "rcs85" / "synthese.json"
DOC_REL = Path("docs") / "49_rcs85_synthese_tp05.md"
STRATEGIES = ("mono-A", "mono-B", "V2")
STATUS_ORDER = {ND: 0, "estimé": 1, "calculé": 2, "mesuré": 3}
SUCCESS_VALUES = {"1", "true", "oui", "yes", "success", "succès", "réussi"}
PRECISION = Decimal("0.000001")
MEASURE_COLUMNS = {
    "case_id", "run_id", "strategy", "model_version", "model_source",
    "status_success", "latency_s", "p95_s", "calls", "retries",
    "input_tokens", "output_tokens", "variable_cost_eur", "allocated_cost_eur",
    "cost_per_success_eur", "energy_kwh", "co2e_kg", "measurement_status",
    "boundary", "source_url", "source_date", "notes",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(raw: Any) -> Optional[Decimal]:
    text = _text(raw)
    if not text or text == ND:
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    return value if value.is_finite() and value >= 0 else None


def _fmt(value: Optional[Decimal]) -> str:
    return ND if value is None else str(value.quantize(PRECISION, rounding=ROUND_HALF_UP))


def _status(raw: Any) -> str:
    value = _text(raw).lower()
    return value if value in STATUS_ORDER else ND


def read_measures(root: Path) -> tuple[List[Dict[str, str]], Dict[str, Any]]:
    path = root / MEASURES_REL
    if not path.is_file():
        raise ValueError(f"Fichier de mesures absent : {MEASURES_REL.as_posix()}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not MEASURE_COLUMNS.issubset(set(reader.fieldnames)):
            missing = MEASURE_COLUMNS - set(reader.fieldnames or [])
            raise ValueError("Colonnes de mesures absentes : " + ", ".join(sorted(missing)))
        rows = [{key: _text(value) for key, value in row.items()} for row in reader]
    provenance = {
        "path": MEASURES_REL.as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rows": len(rows),
    }
    return rows, provenance


def _sourced(row: Dict[str, str]) -> bool:
    return _text(row.get("source_url")) not in ("", ND) and _text(row.get("source_date")) not in ("", ND)


def cost_summary(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    """Coût par tâche réussie : calculé uniquement avec source et succès > 0."""
    summary: Dict[str, Dict[str, Any]] = {}
    for strategy in STRATEGIES:
        selected = [row for row in rows if row.get("strategy") == strategy]
        successes = sum(1 for row in selected if row.get("status_success", "").lower() in SUCCESS_VALUES)
        costs = [
            (_number(row.get("variable_cost_eur")) or Decimal("0"))
            + (_number(row.get("allocated_cost_eur")) or Decimal("0"))
            for row in selected
        ]
        complete = bool(selected) and all(
            _number(row.get("variable_cost_eur")) is not None
            and _number(row.get("allocated_cost_eur")) is not None
            and _sourced(row)
            for row in selected
        )
        sources = sorted({_text(row.get("source_url")) for row in selected if _sourced(row)})
        dates = sorted({_text(row.get("source_date")) for row in selected if _sourced(row)})
        value = sum(costs, Decimal("0")) / successes if complete and successes > 0 else None
        summary[strategy] = {
            "cas": len(selected),
            "succes": successes if selected else ND,
            "appels": str(sum(int(_number(r.get("calls")) or 0) for r in selected)) if selected else ND,
            "retries": str(sum(int(_number(r.get("retries")) or 0) for r in selected)) if selected else ND,
            "cout_variable_eur": _fmt(sum((_number(r.get("variable_cost_eur")) or Decimal("0") for r in selected), Decimal("0"))) if complete else ND,
            "cout_alloue_eur": _fmt(sum((_number(r.get("allocated_cost_eur")) or Decimal("0") for r in selected), Decimal("0"))) if complete else ND,
            "cout_par_succes_eur": _fmt(value),
            "statut": "calculé" if value is not None else ND,
            "source": sources[0] if len(sources) == 1 else (sources if sources else ND),
            "source_date": dates[0] if len(dates) == 1 else (dates if dates else ND),
        }
    return summary


def emission_summary(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    """Énergie/CO₂e : statut le plus faible, jamais zéro pour une donnée absente."""
    summary: Dict[str, Dict[str, Any]] = {}
    for strategy in STRATEGIES:
        selected = [row for row in rows if row.get("strategy") == strategy]
        status = min((_status(row.get("measurement_status")) for row in selected), default=ND, key=lambda s: STATUS_ORDER[s])
        energy = [number for row in selected if (number := _number(row.get("energy_kwh"))) is not None]
        co2 = [number for row in selected if (number := _number(row.get("co2e_kg"))) is not None]
        boundary = sorted({_text(row.get("boundary")) for row in selected if _text(row.get("boundary"))})
        summary[strategy] = {
            "energie_kwh": _fmt(sum(energy, Decimal("0"))) if len(energy) == len(selected) and selected else ND,
            "co2e_kg": _fmt(sum(co2, Decimal("0"))) if len(co2) == len(selected) and selected else ND,
            "statut": status,
            "frontiere": boundary[0] if len(boundary) == 1 else (boundary if boundary else ND),
            "note": "API distante non instrumentée par CodeCarbon local ; aucune valeur n'est mise à zéro.",
        }
    return summary


def residual_risks(root: Path) -> List[Dict[str, str]]:
    """Lit la table « Éthique » du TP05 ; ND si le test n'est pas réalisé."""
    path = root / SOURCE_DOC_REL
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^##\s*4\s*[—-].*?$(.*?)^##\s*5\s", text, re.MULTILINE | re.DOTALL)
    if not match:
        return []
    risks: List[Dict[str, str]] = []
    for line in match.group(1).splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or "risque" in cells[0].lower():
            continue
        risk = re.sub(r"\*\*", "", cells[0]).strip()
        result = cells[-1].upper()
        risks.append({
            "risque": risk,
            "resultat": result if result in {"PASS", "FAIL", ND} else ND,
            "source": SOURCE_DOC_REL.as_posix(),
        })
    return risks


def build_report(root: Path, reviewer: Optional[str] = None) -> Dict[str, Any]:
    rows, provenance = read_measures(root)
    costs = cost_summary(rows)
    emissions = emission_summary(rows)
    risks = residual_risks(root)
    reviewer = reviewer or ND

    if any(risk["resultat"] == "FAIL" for risk in risks):
        decision = "NO_GO"
    elif (
        rows
        and reviewer != ND
        and all(costs[name]["cout_par_succes_eur"] != ND and costs[name]["statut"] in {"mesuré", "calculé"} for name in STRATEGIES)
        and all(emissions[name]["statut"] in {"mesuré", "calculé"} and emissions[name]["co2e_kg"] != ND for name in STRATEGIES)
        and risks
        and all(risk["resultat"] == "PASS" for risk in risks)
    ):
        decision = "GO"
    else:
        decision = "À TESTER"

    # Sans résultat de test (ND), aucun risque ne peut être classé « principal ».
    failed = [risk["risque"] for risk in risks if risk["resultat"] == "FAIL"]
    principal = failed[0] if failed else ND
    return {
        "schema": "rcs85_synthese_tp05/v1",
        "issue": ISSUE,
        "inputs": provenance,
        "comparatif": {
            name: {
                "cout_par_succes_eur": costs[name]["cout_par_succes_eur"],
                "source": costs[name]["source"],
                "source_date": costs[name]["source_date"],
                "statut": costs[name]["statut"],
                "energie_kwh": emissions[name]["energie_kwh"],
                "co2e_kg": emissions[name]["co2e_kg"],
                "statut_emissions": emissions[name]["statut"],
                "frontiere": emissions[name]["frontiere"],
            }
            for name in STRATEGIES
        },
        "detail_couts": costs,
        "detail_emissions": emissions,
        "risques_residuels": risks,
        "risque_principal": principal,
        "decision": decision,
        "reviewer": reviewer,
        "fichiers_versionnes": [
            SOURCE_DOC_REL.as_posix(),
            MEASURES_REL.as_posix(),
            DOC_REL.as_posix(),
            ACCEPTANCE_REL.as_posix(),
        ],
        "limites": [
            "Aucune valeur n'est inventée : le CSV de mesures sert de seule source chiffrée.",
            "Coût par succès ND si succès = 0, coût incomplet ou source absente (jamais 0 €).",
            "Statut énergie = le plus faible des statuts déclarés ; zéro n'est jamais substitué à ND.",
            "Les tests éthiques ND ne valident aucune conformité RGPD/AI Act.",
        ],
        "note": "La synthèse ne remplace ni la revue humaine ni le gel collectif des cas TP04/TP05.",
    }


def serialize(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_doc(report: Dict[str, Any]) -> str:
    lines = [
        f"# {ISSUE} — Synthèse TP05 (coût, émissions, risques, décision)",
        "",
        f"> Décision : **{report['decision']}**. Source chiffrée unique : "
        f"`{MEASURES_REL.as_posix()}` ({report['inputs']['rows']} ligne(s), "
        f"SHA-256 `{report['inputs']['sha256'][:12]}…`). Aucune valeur n'est inventée.",
        "",
        "## Coût par tâche réussie et source",
        "",
        "| Stratégie | Cas | Succès | Coût variable (€) | Coût alloué (€) | Coût/succès (€) | Statut | Source / date |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for name in STRATEGIES:
        item = report["detail_couts"][name]
        lines.append(
            f"| {name} | {item['cas']} | {item['succes']} | {item['cout_variable_eur']} | "
            f"{item['cout_alloue_eur']} | {item['cout_par_succes_eur']} | {item['statut']} | "
            f"{item['source']} / {item['source_date']} |"
        )
    lines += [
        "",
        "## Empreinte Green : état et périmètre",
        "",
        "| Stratégie | Énergie (kWh) | CO₂e (kg) | Statut | Frontière |",
        "|---|---:|---:|---|---|",
    ]
    for name in STRATEGIES:
        item = report["detail_emissions"][name]
        lines.append(
            f"| {name} | {item['energie_kwh']} | {item['co2e_kg']} | {item['statut']} | "
            f"{item['frontiere']} |"
        )
    lines += [
        "",
        report["detail_emissions"]["V2"]["note"],
        "",
        "## Risque résiduel",
        "",
        "| Risque (personnes touchées) | Test / preuve | Source |",
        "|---|---|---|",
    ]
    if report["risques_residuels"]:
        for risk in report["risques_residuels"]:
            lines.append(f"| {risk['risque']} | {risk['resultat']} | `{risk['source']}` |")
    else:
        lines.append(f"| {ND} | {ND} | {ND} |")
    lines += [
        "",
        f"Risque principal : **{report['risque_principal']}**. Un test `ND` signifie non exécuté, pas `PASS`.",
        "",
        "## Décision et limites",
        "",
        f"**{report['decision']}** — relecteur : {report['reviewer']}.",
        "",
    ]
    lines += [f"- {limit}" for limit in report["limites"]]
    lines += [
        f"- {report['note']}",
        "",
        "## Fichiers versionnés et reproduction",
        "",
    ]
    lines += [f"- `{path}`" for path in report["fichiers_versionnes"]]
    lines += [
        "",
        "```bash",
        "python -m tools.rcs85_synthese_tp05 --write",
        "python -m tools.rcs85_synthese_tp05 --reviewer <nom> --write",
        "python -m tools.rcs85_synthese_tp05 --check",
        "python -m unittest tests.test_rcs85_synthese_tp05 -v",
        "```",
        "",
        "Complète `docs/06_tp05_finops_green_ethique.md` (section 5) et `docs/05_tp04_benchmark.md`.",
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
    if report["decision"] == "GO" and report["reviewer"] == ND:
        reasons.append("GO sans relecteur humain")
    if report["decision"] not in {"GO", "NO_GO", "À TESTER"}:
        reasons.append("décision inconnue")
    if report["inputs"]["rows"] == 0 and report["decision"] != "À TESTER":
        reasons.append("synthèse non À TESTER sans mesure versée")
    return not reasons, reasons


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="RCS-85 — synthèse TP05")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--reviewer")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.root, args.reviewer)
    except (OSError, ValueError) as exc:
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
