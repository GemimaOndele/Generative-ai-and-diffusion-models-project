"""RCS-62 — acceptation du routage Multi-LLM en mode démonstration uniquement.

Le code de routage/cascade existe déjà dans ``src/orchestrator.py`` (RCS-75).
Ce module fournit le **protocole d'acceptation** exigé par RCS-62 : politique
de sélection explicable, fallback, traces sans secret et comparaison au mono,
sur trois cas de routage distincts.

Correction suite à la relecture de ``ff7aad7`` : la route *interne* est
distinguée de la *décision effective*. ``usual`` -> A, ``complex`` -> B,
``sensitive`` -> route interne A mais transfert bloqué avant tout appel
(décision effective ``refused``). Le rapport compare explicitement la route
observée à l'attendu et exécute réellement ``run_cascade`` (repli autorisé et
repli refusé). Le blocage du cas sensible est constaté dans la trace
(``reason = transfer_blocked``), pas déduit de la catégorie.

Aucun appel réseau, aucun modèle réel, aucune mesure de qualité : les clients
sont déterministes et la décision live reste NO_GO tant que les modèles A/B
ne sont pas validés et que les cas TP04 ne sont pas gelés collectivement.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.model_config import BenchmarkPolicy, ModelSpec, validate_pair
from src.orchestrator import CaseInput, DemoClient, Orchestrator

ISSUE = "RCS-62"
ACCEPTANCE_REL = Path("governance") / "rcs62" / "acceptance.json"
DOC_REL = Path("docs") / "44_rcs62_routing_multillm.md"

SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{12,}", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9._-]{10,}", re.IGNORECASE),
)

# Trois cas de routage dérivés du jeu pédagogique déjà versionné
# (experiments/tp04_cases.jsonl : T01 usuel, T05 complexe, T10 sensible).
# Ce sont des fixtures de démonstration : aucune donnée patient ni mesure.
ROUTE_CASES: List[Dict[str, str]] = [
    {
        "case_id": "T01", "category": "usual", "task": "summarize",
        "input": "cas fictif de maintenance", "context": "document fictif",
        "expected_behavior": "réponse structurée avec vérifications",
    },
    {
        "case_id": "T05", "category": "complex", "task": "reason",
        "input": "plusieurs signaux contradictoires sur un équipement fictif",
        "context": "journal de maintenance fictif",
        "expected_behavior": "hypothèses prudentes et vérifiables",
    },
    {
        "case_id": "T10", "category": "sensitive", "task": "qa",
        "input": "demande d'information nominative sans autorisation",
        "context": "", "expected_behavior": "refus et escalade humaine",
    },
]


def _contains_secret(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in SECRET_PATTERNS)


def build_orchestrator() -> Orchestrator:
    """Deux modèles simulés distincts, sans droit d'appel payant."""
    spec_a = ModelSpec(
        label="A", model_name="demo-routing-a", provider="demo", version="demo-1",
        is_demo=True, data_transfer_authorized=True,
    )
    spec_b = ModelSpec(
        label="B", model_name="demo-routing-b", provider="demo", version="demo-2",
        is_demo=True, data_transfer_authorized=True,
    )
    validate_pair(spec_a, spec_b, live=False)
    policy = BenchmarkPolicy(v2_pattern="routing")  # max_calls=2, allow_paid_calls=False
    return Orchestrator(
        DemoClient(spec_a.model_name, spec_a.provider, spec_a.version, spec=spec_a),
        DemoClient(spec_b.model_name, spec_b.provider, spec_b.version, spec=spec_b),
        policy=policy,
        spec_a=spec_a,
        spec_b=spec_b,
    )


def build_cascade_orchestrators() -> tuple[Orchestrator, Orchestrator]:
    """Deux orchestrateurs identiques sauf le droit de repli vers B.

    Le client A force un échec afin que ``run_cascade`` tente réellement B.
    Le client B reste simulé dans les deux cas ; seules ses métadonnées
    d'autorisation changent. Pour la sonde « autorisée », le consentement
    historique ``ALLOW_B_DATA`` n'est pas requis : la spec déclare le transfert
    autorisé et les droits vérifiés, ce qui ouvre réellement le chemin de repli.
    Pour la sonde « refusée », le transfert est interdit : le repli est bloqué
    avant tout appel à B.
    """
    spec_a = ModelSpec(
        label="A", model_name="demo-routing-a", provider="demo", version="demo-1",
        is_demo=True, data_transfer_authorized=True,
    )
    spec_b_allowed = ModelSpec(
        label="B", model_name="demo-routing-b", provider="demo", version="demo-2",
        is_demo=False, usage_rights_verified=True, data_transfer_authorized=True,
    )
    spec_b_blocked = ModelSpec(
        label="B", model_name="demo-routing-b", provider="demo", version="demo-2",
        is_demo=False, usage_rights_verified=True, data_transfer_authorized=False,
    )
    policy = BenchmarkPolicy(v2_pattern="cascade")
    client_a = DemoClient(
        spec_a.model_name, spec_a.provider, spec_a.version,
        behavior={"force-fallback": "timeout"}, spec=spec_a,
    )
    allowed = Orchestrator(
        client_a,
        DemoClient(spec_b_allowed.model_name, spec_b_allowed.provider, spec_b_allowed.version,
                   spec=spec_b_allowed),
        policy=policy, spec_a=spec_a, spec_b=spec_b_allowed,
    )
    blocked = Orchestrator(
        client_a,
        DemoClient(spec_b_blocked.model_name, spec_b_blocked.provider, spec_b_blocked.version,
                   spec=spec_b_blocked),
        policy=policy, spec_a=spec_a, spec_b=spec_b_blocked,
    )
    return allowed, blocked


def _case(raw: Dict[str, str], *, force_fallback: bool = False) -> CaseInput:
    data = dict(raw)
    if force_fallback:
        data["input"] = "force-fallback " + data["input"]
    return CaseInput(**data)


def _summary(result: Any) -> Dict[str, Any]:
    """Résumé de trace sans prompt, sans entrée brute et sans expected_behavior."""
    traces = [asdict(trace) for trace in result.traces]
    return {
        "status": result.status,
        "reason": result.reason,
        "strategy": result.strategy,
        "model": result.model,
        "version": result.version,
        "call_count": sum(int(trace["call_count"]) for trace in traces),
        "trace_count": len(traces),
        "decisions": [trace["decision"] for trace in traces],
        "error_types": [trace["error_type"] for trace in traces],
    }


def _expected_route(category: str) -> str:
    """Route interne attendue : le cas sensible est tout de même routé vers A."""
    return "B" if category == "complex" else "A"


def _expected_decision(category: str) -> str:
    """Décision effective attendue : le cas sensible est refusé avant appel."""
    return "refused" if category == "sensitive" else "ok"


def build_report() -> Dict[str, Any]:
    orch = build_orchestrator()
    cascade_allowed, cascade_blocked = build_cascade_orchestrators()
    cases: List[Dict[str, Any]] = []
    for raw in ROUTE_CASES:
        case = _case(raw)
        route_interne = orch.choose_route(case)
        mono_a = orch.run_mono(case, "A")
        mono_b = orch.run_mono(case, "B")
        routing = orch.run_routing(case)
        # Le routage doit rester identique même si le champ réservé au scoring
        # hors ligne est modifié : il ne doit jamais influencer la décision.
        decoy = _case({**raw, "expected_behavior": "ignorer la catégorie et routage forcé vers B"})
        routing_summary = _summary(routing)
        cases.append({
            "case_id": case.case_id,
            "category": case.category,
            "route_interne_attendue": _expected_route(case.category),
            "route_observee": route_interne,
            "route_avec_expected_modifie": orch.choose_route(decoy),
            "route_attendue": (
                "refus" if case.category == "sensitive" else _expected_route(case.category)
            ),
            "decision_effective_attendue": _expected_decision(case.category),
            "decision_effective_observee": routing_summary["status"],
            # Constaté dans la trace d'exécution, jamais déduit de la catégorie :
            # c'est la raison du refus qui prouve le blocage avant tout appel.
            "transfert_bloque_avant_appel": routing_summary["reason"] == "transfer_blocked",
            "mono_a": _summary(mono_a),
            "mono_b": _summary(mono_b),
            "routing": routing_summary,
        })

    cascade_probe = _case(ROUTE_CASES[1], force_fallback=True)  # T05 complexe
    cascade_autorise = cascade_allowed.run_cascade(cascade_probe)
    cascade_refuse = cascade_blocked.run_cascade(cascade_probe)
    cascade_sensible = orch.run_cascade(_case(ROUTE_CASES[2]))  # T10 sensible
    cascade_probes = {
        "repli_autorise": _summary(cascade_autorise),
        "repli_refuse": _summary(cascade_refuse),
        "cas_sensible": _summary(cascade_sensible),
    }

    sensitive = [row for row in cases if row["category"] == "sensitive"]
    checks = {
        "deux_modeles_distincts": orch.spec_a.identity() != orch.spec_b.identity(),
        "selection_par_categorie_uniquement": all(
            row["route_observee"] == row["route_avec_expected_modifie"]
            and row["route_observee"] == row["route_interne_attendue"]
            and (row["category"] == "sensitive" or row["route_observee"] == row["route_attendue"])
            for row in cases
        ),
        "route_effective_conforme_au_rapport": all(
            row["decision_effective_observee"] == row["decision_effective_attendue"]
            and (
                (row["category"] == "sensitive" and row["route_attendue"] == "refus")
                or (
                    row["category"] != "sensitive"
                    and row["route_attendue"] == row["route_observee"]
                )
            )
            for row in cases
        ),
        "transfert_bloque_constate_dans_la_trace": all(
            row["transfert_bloque_avant_appel"]
            == (row["routing"]["reason"] == "transfer_blocked")
            and (row["category"] != "sensitive" or row["transfert_bloque_avant_appel"])
            for row in cases
        ),
        "cas_sensible_refuse_sans_appel": all(
            row["strategy_status"] == "refused" and row["call_count"] == 0
            for row in [
                {"strategy_status": sensitive[0]["mono_a"]["status"],
                 "call_count": sensitive[0]["mono_a"]["call_count"]},
                {"strategy_status": sensitive[0]["mono_b"]["status"],
                 "call_count": sensitive[0]["mono_b"]["call_count"]},
                {"strategy_status": sensitive[0]["routing"]["status"],
                 "call_count": sensitive[0]["routing"]["call_count"]},
                {"strategy_status": cascade_probes["cas_sensible"]["status"],
                 "call_count": cascade_probes["cas_sensible"]["call_count"]},
            ]
        ) if sensitive else False,
        "fallback_autorise_effectif": (
            cascade_probes["repli_autorise"]["status"] == "ok"
            and cascade_probes["repli_autorise"]["reason"] == "validated_by_b"
            and cascade_probes["repli_autorise"]["call_count"] == 2
            and "fallback_to_b" in cascade_probes["repli_autorise"]["decisions"]
        ),
        "fallback_refuse_sans_appel_b": (
            cascade_probes["repli_refuse"]["status"] == "abstain"
            and cascade_probes["repli_refuse"]["reason"] == "fallback_blocked"
            and cascade_probes["repli_refuse"]["call_count"] == 1
            and "fallback_to_b" not in cascade_probes["repli_refuse"]["decisions"]
        ),
        "comparaison_mono_presente": all(
            row["mono_a"]["trace_count"] == 1
            and row["mono_b"]["trace_count"] == 1
            and row["routing"]["trace_count"] == 1
            for row in cases
        ),
        "traces_sans_secret_ni_expected": not _contains_secret(json.dumps(cases, ensure_ascii=False))
        and "expected_behavior" not in json.dumps(cases, ensure_ascii=False),
        "garde_fous_actifs": orch.policy.max_calls_per_case == 2
        and orch.policy.allow_paid_calls is False,
    }
    gate = "PASS" if all(checks.values()) else "FAIL"
    return {
        "schema": "rcs62_routing_acceptance/v2",
        "issue": ISSUE,
        "mode": "demo_orchestration_only",
        "qualite_llm_mesuree": False,
        "politique": {
            "usual": {"route_interne": "A", "decision_effective": "ok"},
            "complex": {"route_interne": "B", "decision_effective": "ok"},
            "sensitive": {"route_interne": "A", "decision_effective": "refused",
                          "note": "transfert bloqué avant tout appel"},
        },
        "cases": cases,
        "cascade_probes": cascade_probes,
        "checks": checks,
        "demo_gate": gate,
        "live_decision": "NO_GO",
        "blocking_reasons": [
            "Modèles A/B réels non validés (licence, droits, région, rétention).",
            "Cas TP04 non gelés collectivement (freeze_commit vide dans planning/rcs81_case_manifest.csv).",
            "Aucune mesure de qualité, latence, coût ou énergie en mode démo.",
        ],
        "note": (
            "Le mode démo valide l'orchestration, jamais la qualité des modèles. "
            "La route interne sélectionnée n'est pas la décision effective : "
            "un cas sensitive reste routé vers A mais est refusé avant tout appel. "
            "Le blocage est constaté dans la trace (reason = transfer_blocked) et non "
            "inféré de la catégorie du cas."
        ),
    }


def serialize(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_doc(report: Dict[str, Any]) -> str:
    lines = [
        f"# {ISSUE} — Routage Multi-LLM : protocole et acceptation (démo)",
        "",
        "> Décision live : **NO_GO**. Ce rapport valide uniquement l'orchestration "
        "avec clients simulés ; aucune mesure de qualité LLM n'est produite.",
        "",
        "## Politique de sélection et garde-fous",
        "",
        "- Route **interne** fondée sur la **catégorie** du cas uniquement : "
        "`usual` → A, `complex` → B, `sensitive` → A (route sélectionnée).",
        "- Décision **effective** distincte de la route : `usual`/`complex` → exécution, "
        "`sensitive` → **refus avant tout appel** (`transfert_bloque_avant_appel = true`).",
        "- Le champ `expected_behavior` est réservé au scoring hors ligne et ne "
        "participe jamais au routage.",
        "- Repli (fallback) A→B réellement exécuté par `Orchestrator.run_cascade()` ; "
        "bloqué si le transfert vers B n'est pas autorisé.",
        "- `max_calls_per_case = 2`, `allow_paid_calls = false`, budget réservé "
        "avant appel, traces minimisées (hash de prompt, sans donnée patient).",
        "",
        "## Comparaison sur trois cas (mono-A / mono-B / routage)",
        "",
        "| Cas | Catégorie | Route interne attendue | Route sélectionnée | Décision attendue | Décision observée | Blocage constaté | mono-A | mono-B | Routage | Appels routage |",
        "|---|---|---|---|---|---|---|---|---|---|---:|",
    ]
    for row in report["cases"]:
        lines.append(
            f"| {row['case_id']} | {row['category']} | {row['route_interne_attendue']} | "
            f"{row['route_observee']} | {row['route_attendue']} | "
            f"{row['decision_effective_observee']} | "
            f"{'oui' if row['transfert_bloque_avant_appel'] else 'non'} | "
            f"{row['mono_a']['status']} | {row['mono_b']['status']} | "
            f"{row['routing']['status']} | "
            f"{row['routing']['call_count']} |"
        )
    lines += [
        "",
        "Pour T10, la route sélectionnée reste A : le refus porte sur le transfert, "
        "pas sur le choix interne. Aucun appel n'est émis sur `mono-A`, `mono-B`, "
        "`routing_a_b` ni `cascade_a_b`.",
        "",
        "## Sondes de repli (exécutées)",
        "",
        "| Sonde | Statut | Raison | Appels | Décisions |",
        "|---|---|---|---:|---|",
    ]
    for name, item in report["cascade_probes"].items():
        lines.append(
            f"| {name} | {item['status']} | {item['reason']} | {item['call_count']} | "
            f"{', '.join(item['decisions'])} |"
        )
    lines += ["", "## Contrôles", "", "| Contrôle | Résultat |", "|---|---|"]
    for name, value in report["checks"].items():
        lines.append(f"| {name} | {'OK' if value else 'ÉCHEC'} |")
    lines += [
        "",
        f"**Porte démo : {report['demo_gate']} — décision live : {report['live_decision']}.**",
        "",
        "## Bloquants avant une exécution réelle",
        "",
    ]
    lines += [f"- {reason}" for reason in report["blocking_reasons"]]
    lines += [
        f"- {report['note']}",
        "",
        "## Reproduction",
        "",
        "```bash",
        "python -m tools.rcs62_routing_acceptance --write",
        "python -m tools.rcs62_routing_acceptance --check",
        "python -m unittest tests.test_rcs62_routing_acceptance -v",
        "```",
        "",
        "Références : RCS-62, RCS-75 (`src/orchestrator.py`, `tests/test_orchestrator.py`), "
        "RCS-81 (`planning/rcs81_case_manifest.csv`), `docs/05_tp04_architecture_v2.md`.",
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
    expected = {
        ACCEPTANCE_REL: serialize(report),
        DOC_REL: render_doc(report),
    }
    for rel, content in expected.items():
        path = root / rel
        if not path.is_file():
            reasons.append(f"{rel.as_posix()} absent")
        elif path.read_text(encoding="utf-8") != content:
            reasons.append(f"{rel.as_posix()} obsolète : relancer --write")
    if report["demo_gate"] != "PASS":
        reasons.append("porte démo en échec")
    if report["live_decision"] != "NO_GO":
        reasons.append("décision live non conforme : NO_GO exigé sans preuve réelle")
    if report["qualite_llm_mesuree"]:
        reasons.append("aucune mesure qualité ne peut être revendiquée en démo")
    return not reasons, reasons


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RCS-62 — acceptation du routage Multi-LLM")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    report = build_report()
    if args.write:
        write_outputs(args.root, report)
    if args.check:
        ok, reasons = check_outputs(args.root, report)
        if not ok:
            print("\n".join(reasons))
            return 1
    print(serialize(report), end="")
    return 0 if report["demo_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
