"""RCS-65 — business case ROI à trois scénarios, calculs vérifiables.

Aucune valeur financière n'est embarquée dans ce dépôt : les hypothèses
livrées sont toutes `ND`. Le module fournit les formules, la propagation de
`ND` et un calculateur déterministe. Une projection reste une hypothèse
sourcée, jamais une mesure, et aucune décision GO n'est produite
automatiquement.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

ND = "ND"
ISSUE = "RCS-65"
SCENARIOS = ("pessimiste", "central", "optimiste")
ALLOWED_STATUS = {"mesuré", "estimé", "hypothèse", ND}
PRECISION = Decimal("0.01")
ACCEPTANCE_REL = Path("governance") / "rcs65" / "business_case.json"
DOC_REL = Path("docs") / "45_rcs65_business_case_roi.md"

HYPOTHESES: Dict[str, str] = {
    "H-01": "volume tâches / mois",
    "H-02": "delta taux de réussite (fraction)",
    "H-03": "gain de temps / tâche réussie (minutes)",
    "H-04": "coût horaire valorisé (EUR/h, hypothétique)",
    "H-05": "coût variable / tâche (EUR, hors postes déjà inclus dans l'API)",
    "H-06": "coûts fixes mensuels non inclus dans le tarif API (EUR)",
    "H-07": "mise en place initiale (EUR)",
    "H-08": "horizon (mois)",
    "H-09": "confirmation absence de double comptage API/infrastructure",
}
NUMERIC_IDS = tuple(key for key in HYPOTHESES if key != "H-09")


@dataclass(frozen=True)
class Hypothesis:
    label: str
    value: Optional[Decimal] = None
    unit: str = ""
    status: str = ND
    source: str = ND
    source_date: str = ND
    owner: str = "Équipe"

    def public(self) -> Dict[str, Any]:
        data = asdict(self)
        data["value"] = ND if self.value is None else str(_round(self.value))
        return data

    def usable(self) -> bool:
        if self.value is None or self.status == ND:
            return False
        if not isinstance(self.source, str) or self.source.strip().casefold() in {"", "nd", "none", "null"}:
            return False
        try:
            return date.fromisoformat(self.source_date).isoformat() == self.source_date
        except (TypeError, ValueError):
            return False


def template_scenario() -> Dict[str, Hypothesis]:
    return {
        key: Hypothesis(label=label, status=ND, source=ND, source_date=ND)
        for key, label in HYPOTHESES.items()
    }


def _round(value: Decimal) -> Decimal:
    return value.quantize(PRECISION, rounding=ROUND_HALF_UP)


def _decimal(raw: Any, key: str) -> Optional[Decimal]:
    if raw is None or str(raw).strip() in ("", ND):
        return None
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{key} doit être un nombre décimal") from exc
    if not value.is_finite() or value < 0:
        raise ValueError(f"{key} doit être fini et >= 0")
    return value


def load_assumptions(path: Optional[str]) -> Dict[str, Dict[str, Hypothesis]]:
    """Charge des hypothèses explicites ; absent = tout ND."""
    scenarios = {name: template_scenario() for name in SCENARIOS}
    if path is None:
        return scenarios
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("scenarios"), dict):
        raise ValueError("Format attendu: {\"scenarios\": {...}}")
    for name, raw_scenario in payload["scenarios"].items():
        if name not in SCENARIOS:
            raise ValueError(f"Scénario inconnu: {name}")
        if not isinstance(raw_scenario, dict):
            raise ValueError(f"Scénario {name} invalide")
        for key, raw in raw_scenario.items():
            if key not in HYPOTHESES or not isinstance(raw, dict):
                raise ValueError(f"Hypothèse inconnue ou mal formée: {name}/{key}")
            status = str(raw.get("status", ND)).strip()
            if status not in ALLOWED_STATUS:
                raise ValueError(f"Statut invalide pour {name}/{key}: {status}")
            value = _decimal(raw.get("value"), f"{name}/{key}") if key != "H-09" else None
            if key == "H-09":
                flag = raw.get("value")
                if flag is None or flag == ND:
                    value = None
                elif type(flag) is bool:
                    value = Decimal("1") if flag else Decimal("0")
                else:
                    raise ValueError("H-09 : booléen JSON strict requis")
            scenarios[name][key] = Hypothesis(
                label=HYPOTHESES[key],
                value=value,
                unit=str(raw.get("unit", "")),
                status=status,
                source=raw.get("source") if isinstance(raw.get("source"), str) else ND,
                source_date=raw.get("source_date") if isinstance(raw.get("source_date"), str) else ND,
                owner=str(raw.get("owner", "Équipe")),
            )
    return scenarios


def scenario_ready(hypotheses: Dict[str, Hypothesis]) -> bool:
    return (all(hypotheses[key].usable() for key in NUMERIC_IDS)
            and hypotheses["H-09"].usable()
            and hypotheses["H-09"].value == Decimal("1")
            and Decimal("0") <= hypotheses["H-02"].value <= Decimal("1"))


def compute_scenario(hypotheses: Dict[str, Hypothesis]) -> Dict[str, Any]:
    """Calcule les formules ; toute donnée manquante reste ND (jamais zéro)."""
    if not scenario_ready(hypotheses):
        return {
            "cout_variable_mensuel_eur": ND,
            "cout_total_mensuel_eur": ND,
            "cout_total_annuel_eur": ND,
            "benefice_annuel_brut_valorise_eur": ND,
            "gain_net_annuel_eur": ND,
            "roi": ND,
            "payback_mois": ND,
            "raison": "hypothèses incomplètes, non sourcées ou double comptage non écarté",
        }
    values = {key: hypotheses[key].value for key in NUMERIC_IDS}
    volume = values["H-01"]
    delta = values["H-02"]
    gain_minutes = values["H-03"]
    hourly = values["H-04"]
    variable = values["H-05"]
    fixed = values["H-06"]
    setup = values["H-07"]
    horizon = values["H-08"]
    if horizon == 0:
        return {
            "cout_variable_mensuel_eur": ND, "cout_total_mensuel_eur": ND,
            "cout_total_annuel_eur": ND, "benefice_annuel_brut_valorise_eur": ND,
            "gain_net_annuel_eur": ND, "roi": ND, "payback_mois": ND,
            "raison": "horizon nul : division par zéro évitée",
        }
    if horizon != Decimal("12"):
        return {
            "cout_variable_mensuel_eur": ND, "cout_total_mensuel_eur": ND,
            "cout_total_annuel_eur": ND, "benefice_annuel_brut_valorise_eur": ND,
            "gain_net_annuel_eur": ND, "roi": ND, "payback_mois": ND,
            "raison": "horizon annuel de 12 mois requis",
        }
    variable_monthly = volume * variable
    total_monthly = fixed + variable_monthly
    total_annual = setup + horizon * total_monthly
    gain_monthly = volume * delta * (gain_minutes / Decimal("60")) * hourly
    gain_annual = gain_monthly * horizon
    net_annual = gain_annual - total_annual
    roi = net_annual / total_annual if total_annual > 0 else None
    # Sans mise de départ, le « temps de retour » n'a pas de sens : ND, pas zéro.
    payback = (
        setup / (gain_monthly - total_monthly)
        if setup > 0 and gain_monthly > total_monthly
        else None
    )
    return {
        "cout_variable_mensuel_eur": str(_round(variable_monthly)),
        "cout_total_mensuel_eur": str(_round(total_monthly)),
        "cout_total_annuel_eur": str(_round(total_annual)),
        "benefice_annuel_brut_valorise_eur": str(_round(gain_annual)),
        "gain_net_annuel_eur": str(_round(net_annual)),
        "roi": ND if roi is None else str(_round(roi)),
        "payback_mois": ND if payback is None else str(_round(payback)),
        "raison": "calcul vérifiable à partir des hypothèses sourcées fournies",
    }


def build_report(assumptions_path: Optional[str] = None, reviewer: Optional[str] = None) -> Dict[str, Any]:
    hypotheses = load_assumptions(assumptions_path)
    scenarios = {
        name: {
            "hypotheses": {key: item.public() for key, item in data.items()},
            "result": compute_scenario(data),
        }
        for name, data in hypotheses.items()
    }
    claim_ready = all(scenario_ready(data) and data["H-08"].value == Decimal("12")
                      for data in hypotheses.values())
    return {
        "schema": "rcs65_business_case/v1",
        "issue": ISSUE,
        "devise": "EUR",
        "formules": {
            "cout_variable_mensuel": "volume * cout_variable_par_tache",
            "cout_total_mensuel": "couts_fixes_non_inclus_API + cout_variable_mensuel",
            "cout_total_annuel": "mise_en_place + horizon * cout_total_mensuel",
            "benefice_annuel_brut_valorise": "volume * horizon * delta_taux_reussite * (gain_minutes/60) * cout_horaire_hypothetique",
            "gain_net_annuel": "benefice_annuel_brut_valorise - cout_total_annuel",
            "roi": "gain_net_annuel / cout_total_annuel (ND si dénominateur nul)",
            "payback_mois": "mise_en_place / (benefice_mensuel - cout_total_mensuel) (ND si net mensuel <= 0)",
        },
        "scenarios": scenarios,
        "claim_ready": claim_ready,
        "financial_claim": False,
        "decision": "À VALIDER" if claim_ready else ND,
        "reviewer": reviewer or ND,
        "blocking_reasons": [
            "Hypothèses toutes ND : volume, taux de réussite, tarifs et effort restent à sourcer.",
            "Tant que les scénarios ne sont pas sourcés et relus, aucune projection n'est une mesure.",
            "Le temps étudiant est une valorisation hypothétique, pas une dépense facturée.",
            "Le double comptage infrastructure/tarif API doit être explicitement écarté.",
        ],
        "note": "Aucun GO automatique : la décision financière appartient à l'équipe après revue humaine.",
    }


def serialize(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_doc(report: Dict[str, Any]) -> str:
    lines = [
        f"# {ISSUE} — Business case ROI à trois scénarios",
        "",
        "> Les valeurs livrées sont `ND` : aucune hypothèse financière n'est "
        "inventée et aucune projection n'est présentée comme une mesure. "
        "Décision automatique : "
        f"**{report['decision']}**, revue humaine obligatoire.",
        "",
        "## Formules vérifiables",
        "",
    ]
    for name, formula in report["formules"].items():
        lines.append(f"- `{name}` = {formula}")
    lines += [
        "",
        "Règles : EUR uniquement (aucune conversion implicite), "
        "`ND` plutôt que zéro. Pas de double comptage des postes déjà inclus dans le tarif API.",
        "",
        "## Hypothèses et résultats",
        "",
        "| ID | Hypothèse | Pessimiste | Central | Optimiste | Statut/source |",
        "|---|---|---|---|---|---|",
    ]
    first = next(iter(report["scenarios"].values()))
    for key, item in first["hypotheses"].items():
        values = [scenario["hypotheses"][key] for scenario in report["scenarios"].values()]
        status = "/".join(sorted({row["status"] for row in values}))
        source = "/".join(sorted({row["source"] for row in values}))
        cells = [str(row["value"]) for row in values]
        lines.append(
            f"| {key} | {item['label']} | {cells[0]} | {cells[1]} | {cells[2]} | "
            f"{status} / {source} |"
        )
    lines += ["", "| Résultat | Pessimiste | Central | Optimiste |", "|---|---|---|---|"]
    result_keys = (
        "cout_variable_mensuel_eur", "cout_total_mensuel_eur", "cout_total_annuel_eur",
        "benefice_annuel_brut_valorise_eur", "gain_net_annuel_eur", "roi", "payback_mois",
    )
    for key in result_keys:
        cells = [str(scenario["result"][key]) for scenario in report["scenarios"].values()]
        lines.append(f"| {key} | {cells[0]} | {cells[1]} | {cells[2]} |")
    lines += [
        "",
        "## Limites et décision",
        "",
    ]
    lines += [f"- {reason}" for reason in report["blocking_reasons"]]
    lines += [
        f"- Décision automatique : **{report['decision']}** ; relecteur : {report['reviewer']}.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "python -m tools.rcs65_business_case --write",
        "python -m tools.rcs65_business_case --check",
        "python -m tools.rcs65_business_case --assumptions <fichier.json> --write",
        "python -m unittest tests.test_rcs65_business_case -v",
        "```",
        "",
        "Lien avec RCS-90 (`tools/rcs90_finops.py`, coûts complets), RCS-82 "
        "(`experiments/results/tp05_mesures.csv`, coût par tâche réussie) et ADR-002 "
        "(ne pas publier d'estimation comme mesure).",
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


def check_outputs(root: Path, report: Dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for rel, content in (
        (ACCEPTANCE_REL, serialize(report)),
        (DOC_REL, render_doc(report)),
    ):
        path = root / rel
        if not path.is_file():
            reasons.append(f"{rel.as_posix()} absent")
        elif path.read_text(encoding="utf-8") != content:
            reasons.append(f"{rel.as_posix()} obsolète : relancer --write")
    if report["financial_claim"]:
        reasons.append("une projection ne peut pas être déclarée comme mesure")
    if report["decision"] == "GO":
        reasons.append("décision GO interdite sans revue humaine")
    return not reasons, reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RCS-65 — business case ROI trois scénarios")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--assumptions")
    parser.add_argument("--reviewer")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.assumptions, args.reviewer)
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
