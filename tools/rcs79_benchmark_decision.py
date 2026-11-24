"""RCS-79 — synthèse benchmark V2 et décision traçable (révision technique).

Durcissement appliqué à la suite de la relecture de ``5a1cf06`` :
- schémas JSON stricts (aucune clé inattendue, types et formats explicites) ;
- valeurs numériques finies, non booléennes, bornées selon leur unité ;
- identités de modèles canoniques (ni ``ND``/``None``, ni espaces) ;
- résultats liés au manifeste RCS-81 (dix identifiants et empreintes), à la config,
  au run et au commit déclarés ; cohérence interne distincte de l'authentification
  externe des références, toujours bloquée hors ligne ; approbation des seuils
  antérieure à l'exécution ;
- revue indépendante **déclarée** (rôle, auteurs, date et commit cohérents),
  sans qualifier une chaîne textuelle de signature vérifiée ;
- porte bloquée sur la vérification humaine externe de la revue et sur
  l'autorisation collective ; aucune décision GO automatisée.

Une chaîne de signature n'est pas vérifiée cryptographiquement par cet outil :
elle ne peut pas lever la porte de vérification. Sans preuves conformes, la
décision reste NO_GO ; avec des preuves conformes mais sans vérification
humaine externe documentée, elle reste A_TESTER.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.rcs81_evaluate import CASE_COLUMNS, IDS, check_manifest, csv_rows

ND = "ND"
ISSUE = "RCS-79"
SCHEMA_DECISION = "rcs79_benchmark_decision/v2"
SCHEMA_MODELS = "rcs79_models/v1"
SCHEMA_RESULTS = "rcs79_live_results/v1"
SCHEMA_REVIEW = "rcs79_independent_review_declaration/v2"
DEFAULT_MANIFEST = Path("planning") / "rcs81_case_manifest.csv"
ACCEPTANCE_REL = Path("governance") / "rcs79" / "decision.json"
DOC_REL = Path("docs") / "48_rcs79_benchmark_decision.md"
STRATEGIES = ("mono-A", "mono-B", "V2")
REQUIRED_METRICS = ("quality", "p95_ms", "cost_eur", "co2e_kg", "energy_status")
MODEL_FIELDS = ("model_name", "provider", "version", "license", "region", "retention_policy")
ENERGY_STATUSES = {"mesuré", "calculé", "estimé"}
REVIEW_DECISIONS = {"GO", "GO_WITH_RESERVATIONS", "GO_AVEC_RESERVES"}

# Bornes explicites par unité : la qualité est une fraction, pas un pourcentage.
METRIC_BOUNDS = {
    "quality": (0.0, 1.0),
    "quality_delta": (0.0, 1.0),
    "p95_ms": (0.0, 86_400_000.0),      # 24 h, au-delà la donnée est suspecte
    "cost_eur": (0.0, 1_000_000_000.0),
    "co2e_kg": (0.0, 1_000_000_000.0),
}
HEX_SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")
NAME_PATTERN = re.compile(r"[A-Za-z0-9._-]{2,64}")
RUN_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{2,63}")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
DATETIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _load_json(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if path is None:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} doit contenir un objet JSON")
    return payload


def _canonical_text(value: Any, pattern: Optional[re.Pattern[str]] = None) -> Optional[str]:
    """Texte non vide, ni ND/None/null, sans espaces de bord, au format attendu."""
    if not isinstance(value, str):
        return None
    if value != value.strip() or value in ("", ND):
        return None
    if value.lower() in {"none", "null", "nan", "inf", "+inf", "-inf"}:
        return None
    if pattern and not pattern.fullmatch(value):
        return None
    return value


def _number(value: Any, metric: Optional[str] = None) -> Optional[float]:
    """Nombre JSON strict : ni booléen, ni chaîne, ni NaN/infini, borné par unité."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    bounds = METRIC_BOUNDS.get(metric) if metric else None
    if bounds and not (bounds[0] <= number <= bounds[1]):
        return None
    return number


def _sha(value: Any) -> Optional[str]:
    return _canonical_text(value, HEX_SHA)


def _date(value: Any) -> Optional[date]:
    text = _canonical_text(value, DATE_PATTERN)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _datetime_date(value: Any) -> Optional[date]:
    text = _canonical_text(value, DATETIME_PATTERN)
    if text is None:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _strict(payload: Optional[Dict[str, Any]], required: set[str], optional: set[str] = frozenset()) -> bool:
    if not isinstance(payload, dict):
        return False
    keys = set(payload)
    return required <= keys and keys <= (required | set(optional))


def manifest_fingerprint(path: Path) -> Optional[str]:
    """SHA-256 du manifeste normalisé LF (identique Windows/Linux)."""
    try:
        raw = path.read_bytes().replace(b"\r\n", b"\n")
    except OSError:
        return None
    return hashlib.sha256(raw).hexdigest()


def models_valid(
    payload: Optional[Dict[str, Any]], manifest_sha256: Optional[str] = None
) -> bool:
    if not _strict(payload, {
        "schema", "config_sha256", "manifest_sha256", "A", "B",
    }):
        return False
    assert payload is not None
    if payload["schema"] != SCHEMA_MODELS:
        return False
    if _sha(payload["manifest_sha256"]) is None or (
        manifest_sha256 is not None and payload["manifest_sha256"] != manifest_sha256
    ):
        return False
    if _sha(payload["config_sha256"]) is None:
        return False
    identities = set()
    for label in ("A", "B"):
        spec = payload[label]
        required = set(MODEL_FIELDS) | {
            "validated", "usage_rights_verified", "data_transfer_authorized",
            "validation_source", "validation_date",
        }
        if not _strict(spec, required):
            return False
        if spec.get("validated") is not True or spec.get("usage_rights_verified") is not True:
            return False
        if spec.get("data_transfer_authorized") is not True:
            return False
        if _canonical_text(spec["validation_source"]) is None or _date(spec["validation_date"]) is None:
            return False
        for field in ("license", "region", "retention_policy"):
            if _canonical_text(spec[field]) is None:
                return False
        identity = tuple(
            _canonical_text(spec[field], ID_PATTERN) for field in ("provider", "model_name", "version")
        )
        if any(part is None for part in identity):
            return False
        identities.add(identity)
    return len(identities) == 2


def cases_linked(
    payload: Optional[Dict[str, Any]], rows: List[Dict[str, str]], manifest_sha256: Optional[str]
) -> bool:
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        return False
    declared = payload["cases"]
    if len(declared) != 10 or len(rows) != 10:
        return False
    if isinstance(payload.get("cases_count"), bool) or payload.get("cases_count") != 10:
        return False
    if _sha(payload.get("manifest_sha256")) != manifest_sha256:
        return False
    expected = {row["case_id"]: row["freeze_commit"] for row in rows}
    if sorted(expected) != sorted(IDS):
        return False
    seen: Dict[str, str] = {}
    for item in declared:
        if not _strict(item, {"case_id", "freeze_commit"}):
            return False
        case_id = _canonical_text(item["case_id"], ID_PATTERN)
        freeze = _sha(item["freeze_commit"])
        if case_id is None or freeze is None or case_id in seen:
            return False
        seen[case_id] = freeze
    return seen == expected


def thresholds_valid(payload: Optional[Dict[str, Any]], executed_at: Optional[date]) -> bool:
    if not isinstance(payload, dict):
        return False
    thresholds = payload.get("approved_thresholds")
    if not _strict(thresholds, {
        "quality_delta", "p95_ms", "cost_eur", "approved_at", "approved_by", "evidence",
    }):
        return False
    assert thresholds is not None
    for key in ("quality_delta", "p95_ms", "cost_eur"):
        if _number(thresholds[key], key) is None:
            return False
    if _date(thresholds["approved_at"]) is None or _canonical_text(thresholds["approved_by"], NAME_PATTERN) is None:
        return False
    if _canonical_text(thresholds["evidence"]) is None or executed_at is None:
        return False
    approved = _date(thresholds["approved_at"])
    return approved is not None and approved < executed_at


def run_linked(payload: Optional[Dict[str, Any]], config_sha256: Optional[str], commit: Optional[str]) -> bool:
    if not isinstance(payload, dict):
        return False
    if _canonical_text(payload.get("run_id"), RUN_PATTERN) is None:
        return False
    if _sha(payload.get("config_sha256")) != config_sha256:
        return False
    if _sha(payload.get("commit")) != commit or _sha(commit) is None:
        return False
    if _canonical_text(payload.get("run_evidence")) is None:
        return False
    strategies = payload.get("strategies")
    if not isinstance(strategies, dict) or set(strategies) != set(STRATEGIES):
        return False
    for item in strategies.values():
        if not _strict(item, {
            "run_id", "quality", "p95_ms", "cost_eur", "co2e_kg",
            "energy_status", "trace_evidence",
        }):
            return False
        if item["run_id"] != payload["run_id"]:
            return False
        if _canonical_text(item["trace_evidence"]) is None:
            return False
        if item["energy_status"] not in ENERGY_STATUSES:
            return False
        for key in ("quality", "p95_ms", "cost_eur", "co2e_kg"):
            if _number(item[key], key) is None:
                return False
    return True


def results_valid(
    payload: Optional[Dict[str, Any]],
    *,
    rows: List[Dict[str, str]],
    manifest_sha256: Optional[str],
    config_sha256: Optional[str],
    commit: Optional[str],
) -> bool:
    if not _strict(payload, {
        "schema", "execution_mode", "cases_count", "executed_at", "manifest_sha256",
        "config_sha256", "run_id", "commit", "run_evidence", "cases", "strategies",
        "approved_thresholds",
    }):
        return False
    assert payload is not None
    if payload["schema"] != SCHEMA_RESULTS or payload["execution_mode"] != "live":
        return False
    if _datetime_date(payload["executed_at"]) is None:
        return False
    return (
        cases_linked(payload, rows, manifest_sha256)
        and run_linked(payload, config_sha256, commit)
        and thresholds_valid(payload, _datetime_date(payload["executed_at"]))
    )


def review_declaration_valid(
    payload: Optional[Dict[str, Any]], *, reviewer: str, commit: str, executed_at: Optional[date]
) -> bool:
    """Présence d'une déclaration de revue indépendante, pas preuve de signature.

    Le champ ``declaration`` est un texte libre : il ne fait l'objet d'aucune
    vérification cryptographique. Cette fonction contrôle uniquement la
    cohérence formelle (rôle indépendant, relecteur absent des auteurs, date,
    commit et avis). La vérification de l'identité et du document signé reste
    une porte humaine externe, toujours bloquée dans cet outil hors ligne.
    """
    if not _strict(payload, {
        "schema", "reviewer", "role", "reviewed_at", "decision", "declaration", "commit", "authors",
    }):
        return False
    assert payload is not None
    if payload["schema"] != SCHEMA_REVIEW:
        return False
    if _canonical_text(payload["reviewer"], NAME_PATTERN) != reviewer or _sha(payload["commit"]) != commit:
        return False
    role = _canonical_text(payload["role"])
    if role is None or role.lower() not in {"independent", "indépendant"}:
        return False
    if payload["decision"] not in REVIEW_DECISIONS:
        return False
    if _canonical_text(payload["declaration"]) is None:
        return False
    reviewed_at = _date(payload["reviewed_at"])
    authors = payload["authors"]
    if not isinstance(authors, list) or not authors:
        return False
    if any(not isinstance(name, str) for name in authors):
        return False
    if reviewer.lower() in {name.lower() for name in authors}:
        return False
    return reviewed_at is not None and executed_at is not None and reviewed_at >= executed_at


def recommendation_ready(gates: Dict[str, bool]) -> bool:
    """Vrai seulement si toutes les portes, y compris la vérification humaine, sont levées."""
    return bool(gates) and not gates.get("autorisation_collective", True) and all(
        value for key, value in gates.items() if key != "autorisation_collective"
    )


def build_report(
    root: Path,
    manifest: Optional[str] = None,
    results: Optional[str] = None,
    models: Optional[str] = None,
    reviewer: Optional[str] = None,
    commit: Optional[str] = None,
    review_declaration: Optional[str] = None,
) -> Dict[str, Any]:
    manifest_path = Path(manifest) if manifest else root / DEFAULT_MANIFEST
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    fingerprint = manifest_fingerprint(manifest_path)
    try:
        rows = csv_rows(manifest_path, CASE_COLUMNS)
        cases_frozen, case_blockers = check_manifest(rows)
    except (OSError, ValueError):
        rows, cases_frozen = [], False
        case_blockers = ["Manifeste RCS-81 absent ou invalide"]

    models_payload = _load_json(models)
    results_payload = _load_json(results)
    review_payload = _load_json(review_declaration)
    reviewer = _canonical_text(reviewer, NAME_PATTERN) or ND
    commit = _sha(commit) or ND
    config_sha256 = models_payload.get("config_sha256") if models_payload else None
    executed_at = _datetime_date(results_payload.get("executed_at")) if results_payload else None

    valid_models = models_valid(models_payload, fingerprint)
    valid_results = results_valid(
        results_payload,
        rows=rows,
        manifest_sha256=fingerprint,
        config_sha256=config_sha256 if valid_models else None,
        commit=commit,
    )
    declared_review = review_declaration_valid(
        review_payload, reviewer=reviewer, commit=commit, executed_at=executed_at
    )
    linked_cases = cases_linked(results_payload, rows, fingerprint)
    linked_run = run_linked(results_payload, config_sha256 if valid_models else None, commit)
    approved_thresholds = thresholds_valid(results_payload, executed_at)

    comparatif: Dict[str, Dict[str, Any]] = {}
    for name in STRATEGIES:
        if valid_results:
            item = results_payload["strategies"][name]
            comparatif[name] = {key: item[key] for key in REQUIRED_METRICS}
        else:
            comparatif[name] = {key: ND for key in REQUIRED_METRICS}

    gates: Dict[str, bool] = {
        "cas_geles": cases_frozen,
        "modeles_ab_valides": valid_models,
        "resultats_live_reels": valid_results,
        "preuves_manifeste_config_run": linked_cases and linked_run,
        "seuils_approuves_avant_resultats": approved_thresholds,
        "declaration_revue_independante": declared_review,  # présence seulement, pas une preuve
        "reference_commit_declaree": bool(commit != ND and linked_run and results_payload
                                          and results_payload.get("commit") == commit),
        # Cohérence interne des chaînes seulement : sans vérification humaine
        # externe, ni le commit, ni le hash de config, ni le run ne sont authentifiés.
        "authentification_references_externes": False,
        # Une chaîne textuelle n'est pas une signature vérifiable : la porte
        # reste bloquée jusqu'à une vérification humaine externe documentée.
        "verification_humaine_externe_signature": False,
        "autorisation_collective": False,  # hors ligne : jamais vérifiable par cet outil
        "qualite_v2_superieure": False,
        "latence_conforme": False,
        "cout_conforme": False,
        "energie_documentee": False,
    }
    if valid_results:
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
            results_payload["strategies"][name]["energy_status"] in {"mesuré", "calculé"}
            for name in STRATEGIES
        )

    if not (gates["cas_geles"] and gates["modeles_ab_valides"]):
        decision = "NO_GO"
    elif recommendation_ready(gates):
        decision = "RECOMMANDATION_A_RATIFIER"
    else:
        decision = "A_TESTER"

    blocking_reasons: List[str] = []
    if not gates["cas_geles"]:
        blocking_reasons.append("Cas RCS-81 non gelés collectivement : freeze_commit absent ou invalide.")
    if not gates["modeles_ab_valides"]:
        blocking_reasons.append(
            "Modèles A/B non conformes : schéma strict, identités canoniques, licence/droits/région/"
            "rétention, preuve de validation, manifeste commun et hash de config requis."
        )
    if not gates["resultats_live_reels"]:
        blocking_reasons.append(
            "Résultats live non conformes : dix cas et empreintes du manifeste, run, commit, config, "
            "valeurs finies bornées et schéma strict exigés."
        )
    if not gates["preuves_manifeste_config_run"]:
        blocking_reasons.append("Preuves non liées au même manifeste/config/run/commit.")
    if not gates["seuils_approuves_avant_resultats"]:
        blocking_reasons.append("Seuils approuvés absents, non sourcés ou approuvés après l'exécution.")
    if not gates["declaration_revue_independante"]:
        blocking_reasons.append(
            "Déclaration de revue indépendante absente ou non conforme : rôle indépendant, "
            "relecteur absent des auteurs, date et commit requis."
        )
    if not gates["verification_humaine_externe_signature"]:
        blocking_reasons.append(
            "Vérification humaine externe de la revue non documentée : une déclaration ou une "
            "chaîne de signature textuelle n'est pas une preuve vérifiable."
        )
    if not gates["reference_commit_declaree"]:
        blocking_reasons.append(
            "Référence commit absente, tronquée ou différente de celle déclarée par le run."
        )
    if not gates["authentification_references_externes"]:
        blocking_reasons.append(
            "Authentification externe des références non documentée : la cohérence interne entre "
            "commit, hash de config et run n'atteste ni identité ni origine."
        )
    for key, reason in (
        ("qualite_v2_superieure", "Gain V2 inférieur au seuil approuvé ou donnée invalide."),
        ("latence_conforme", "p95 V2 supérieure au seuil approuvé ou donnée invalide."),
        ("cout_conforme", "Coût V2 supérieur au seuil approuvé ou donnée invalide."),
        ("energie_documentee", "Énergie/CO₂e non documentée ou non calculée sur un périmètre commun."),
    ):
        if not gates[key]:
            blocking_reasons.append(reason)
    blocking_reasons.append(
        "Autorisation collective non vérifiée : l'outil ne peut émettre qu'une recommandation "
        "à ratifier par l'équipe, jamais un GO."
    )
    if case_blockers and not gates["cas_geles"]:
        blocking_reasons.extend(case_blockers[:2])

    return {
        "schema": SCHEMA_DECISION,
        "issue": ISSUE,
        "inputs": {
            "manifest": manifest_path.as_posix(),
            "manifest_sha256": fingerprint or ND,
            "results": results or ND,
            "models": models or ND,
            "review_declaration": review_declaration or ND,
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
        "note": (
            "Aucune décision GO automatisée. Une déclaration de revue n'est pas une signature "
            "vérifiée, et la cohérence interne des références (commit, config, run) n'est pas une "
            "authentification : la vérification humaine externe et l'autorisation collective "
            "restent à documenter, donc au mieux A_TESTER dans cet outil. Un mock ou le mode "
            "démo ne peut jamais étayer une recommandation."
        ),
    }


def serialize(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_doc(report: Dict[str, Any]) -> str:
    lines = [
        f"# {ISSUE} — Benchmark V2 Multi-LLM et décision traçable",
        "",
        "> Ce document est généré à partir de preuves strictement validées. "
        "Sans gel RCS-81 ni modèles conformes, la décision est **NO_GO** ; "
        "avec des preuves conformes mais sans vérification humaine externe documentée, "
        "elle reste **A_TESTER**. La revue indépendante n'est qu'une déclaration : "
        "aucune chaîne de signature n'est vérifiée ici et aucune recommandation ne peut "
        "être émise sans vérification humaine et ratification collective. Aucune valeur n'est simulée.",
        "",
        "## Comparatif mono / V2",
        "",
        "| Stratégie | Qualité (fraction) | p95 (ms) | Coût (€) | CO₂e (kg) | Statut énergie |",
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
        "## Schémas et bornes exigés",
        "",
        f"- Résultats : `{SCHEMA_RESULTS}` ; modèles : `{SCHEMA_MODELS}` ; "
        f"revue : `{SCHEMA_REVIEW}`.",
        "- Numériques : types JSON uniquement, booléens refusés, finis, ≥ 0 et bornés "
        "(qualité et delta ∈ [0, 1] ; p95 ≤ 86 400 000 ms).",
        "- Preuves : hash du manifeste, hash de config, `run_id`, commit complet, "
        "dix `case_id`/`freeze_commit`, approbation des seuils avant `executed_at` et "
        "déclaration de revue indépendante (relecteur absent des auteurs). "
        "Le champ `declaration` n'est pas vérifié cryptographiquement : une signature "
        "textuelle ne lève pas la porte `verification_humaine_externe_signature`. "
        "De même, `reference_commit_declaree` n'atteste pas l'origine du commit, du hash "
        "de config ou du run : `authentification_references_externes` reste BLOQUÉ.",
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
        "--review-declaration <declaration.json> --reviewer <nom> --commit <sha40|sha64> --write",
        "python -m tools.rcs79_benchmark_decision --check",
        "python -m unittest tests.test_rcs79_benchmark_decision -v",
        "```",
        "",
        "Le rapport complète `docs/05_tp04_benchmark.md` et le protocole RCS-81, "
        "sans remplacer la ratification collective ni le gel des cas.",
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
    if report["decision"] == "GO":
        reasons.append("GO interdit : seule une recommandation à ratifier peut être émise")
    if report["decision"] not in {"NO_GO", "A_TESTER", "RECOMMANDATION_A_RATIFIER"}:
        reasons.append("décision inconnue")
    gates = report["gates"]
    if gates.get("revue_independante_attestee") is not None:
        reasons.append("porte « revue attestée » supprimée : la revue n'est qu'une déclaration")
    if gates.get("verification_humaine_externe_signature") is not False:
        reasons.append("vérification humaine externe non vérifiable hors ligne : porte bloquée obligatoire")
    if gates.get("authentification_references_externes") is not False:
        reasons.append("authentification externe des références non vérifiable hors ligne : porte bloquée obligatoire")
    if gates.get("commit_reference") is not None:
        reasons.append("porte « commit_reference » supprimée : la référence n'est que déclarée")
    if report["decision"] == "RECOMMANDATION_A_RATIFIER" and not recommendation_ready(gates):
        reasons.append("recommandation sans toutes les portes ou avec vérification/ratification simulée")
    if report["decision"] == "A_TESTER" and recommendation_ready(gates):
        reasons.append("portes levées : la recommandation à ratifier est attendue")
    return not reasons, reasons


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RCS-79 — décision benchmark V2 (schéma strict)")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest")
    parser.add_argument("--results")
    parser.add_argument("--models")
    parser.add_argument("--review-declaration", dest="review_declaration")
    parser.add_argument("--review-evidence", dest="review_declaration",
                        help="alias historique de --review-declaration")
    parser.add_argument("--reviewer")
    parser.add_argument("--commit")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            args.root, args.manifest, args.results, args.models,
            args.reviewer, args.commit, args.review_declaration,
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
