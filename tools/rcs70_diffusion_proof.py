"""RCS-70 — manifeste de preuve pour une diffusion réellement débruitée.

L'outil n'entraîne rien et n'invente aucun résultat : il audite le code de
débruitage déjà fusionné (PR #7) et, si un artefact JSON réel est fourni,
copie uniquement les champs qu'il contient avec son SHA-256. Sans artefact,
toutes les preuves restent `ND` et la décision reste `A_TESTER`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

ND = "ND"
ISSUE = "RCS-70"
SCRIPT_REL = Path("experiments") / "rcs69_diffusion_numpy.py"
ACCEPTANCE_REL = Path("governance") / "rcs70" / "proof_manifest.json"
DOC_REL = Path("docs") / "47_rcs70_diffusion_preuve.md"

EVIDENCE_KEYS = (
    "seed", "numpy_version", "diffusion_timesteps", "train_updates",
    "dataset_sha256", "training_runtime_seconds", "generated_samples_count",
    "sample_finite", "scope", "scientific_status", "training_method",
    "train_loss_start", "train_loss_end",
)
METRIC_KEYS = ("baseline_MAD", "learned_diffusion_denoiser")
ALLOWED_PAYLOAD_KEYS = frozenset(EVIDENCE_KEYS) | frozenset(METRIC_KEYS)
FORBIDDEN_KEYS = ("patient", "diagnostic", "identifier", "nom", "surname")


def structure_checks(source: str) -> Dict[str, bool]:
    """Indices lexicaux uniquement : ne prouvent ni entraînement ni exécution."""
    lowered = source.lower()
    return {
        "indices_textuels_train": "denoiser" in lowered and "def train(" in lowered and "epsilon" in lowered,
        "indices_textuels_sampler": "def sample(" in lowered and "reverse" in lowered and "ddpm" in lowered,
        "seed_explicite": "seed" in lowered,
        "indices_textuels_reverse": "learned" in lowered and "reverse" in lowered,
    }


def _finite(value: Any, maximum: float | None = None) -> bool:
    return (type(value) in (int, float) and math.isfinite(value)
            and value >= 0 and (maximum is None or value <= maximum))


def _valid_evidence(key: str, value: Any) -> bool:
    if key in {"seed", "diffusion_timesteps", "train_updates", "generated_samples_count"}:
        return type(value) is int and value >= (0 if key == "seed" else 1)
    if key in {"training_runtime_seconds", "train_loss_start", "train_loss_end"}:
        return _finite(value)
    if key == "sample_finite":
        return value is True
    if key == "dataset_sha256":
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    if key == "numpy_version":
        return isinstance(value, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", value) is not None
    return value == {
        "scope": "synthetic_signal_research_only_not_medical",
        "scientific_status": "illustrative_experiment_not_clinical_validation",
        "training_method": "learned_epsilon_MLP_Adam_DDPM_reverse_sampler",
    }.get(key)


def _valid_metrics(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    counts = {"TP", "FP", "TN", "FN"}
    ratios = {"precision", "recall", "f1", "false_alarm_rate"}
    threshold = "threshold_validation_normal_95pct"
    return (set(value) == counts | ratios | {threshold}
            and all(type(value[k]) is int and value[k] >= 0 for k in counts)
            and sum(value[k] for k in counts) > 0
            and all(value[k] is None or _finite(value[k], 1) for k in ratios)
            and _finite(value[threshold]))


def forbidden_markers(node: Any) -> List[str]:
    """Cherche récursivement les marqueurs sensibles dans clés et valeurs."""
    found: List[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            label = str(key).lower()
            found.extend(marker for marker in FORBIDDEN_KEYS if marker in label)
            found.extend(forbidden_markers(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(forbidden_markers(value))
    elif isinstance(node, str):
        lowered = node.lower()
        found.extend(marker for marker in FORBIDDEN_KEYS if marker in lowered)
    return found


def read_artifact(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("L'artefact doit être un objet JSON")
    return payload


def build_report(root: Path, artifact: str | None = None) -> Dict[str, Any]:
    script = root / SCRIPT_REL
    source = script.read_text(encoding="utf-8") if script.is_file() else ""
    checks = structure_checks(source)
    evidence: Dict[str, Any] = {key: ND for key in EVIDENCE_KEYS}
    metrics: Dict[str, Any] = {key: ND for key in METRIC_KEYS}
    artifact_info: Dict[str, Any] = {
        "path": ND, "sha256": ND, "present": False,
    }
    payload: Dict[str, Any] | None = None
    if artifact is not None:
        artifact_path = Path(artifact)
        if not artifact_path.is_absolute():
            artifact_path = root / artifact_path
        if not artifact_path.is_file():
            raise ValueError(f"Artefact introuvable: {artifact_path}")
        payload = read_artifact(artifact_path)
        artifact_info = {
            "path": artifact_path.as_posix(),
            "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            "present": True,
        }
        for key in EVIDENCE_KEYS:
            if key in payload and _valid_evidence(key, payload[key]):
                evidence[key] = payload[key]
        for key in METRIC_KEYS:
            if key in payload and _valid_metrics(payload[key]):
                metrics[key] = payload[key]

    forbidden = forbidden_markers(payload) if payload is not None else []
    unexpected = sorted(set(payload) - ALLOWED_PAYLOAD_KEYS) if payload is not None else []
    strict_schema = not artifact_info["present"] or (not unexpected and not forbidden)
    checks.update({
        "structure_textuelle_presente": all(structure_checks(source).values()),
        "artefact_present": artifact_info["present"],
        "schema_artefact_strict": strict_schema,
        "artefact_complet": artifact_info["present"] and strict_schema and all(
            evidence[key] not in (ND, None, "") for key in EVIDENCE_KEYS
        ) and all(metrics[key] != ND for key in METRIC_KEYS),
        "perimetre_synthetique_declare": str(evidence["scope"]).startswith("synthetic")
        and "not_clinical" in str(evidence["scientific_status"]),
        "champs_exportes_autorises": not forbidden and "patient" not in json.dumps(metrics, ensure_ascii=False).lower(),
    })
    if not checks["structure_textuelle_presente"]:
        proof_status = "BLOQUE"
    elif not artifact_info["present"]:
        proof_status = "ND"
    elif all(checks.values()):
        proof_status = "DECLARATION_NON_AUTHENTIFIEE"
    else:
        proof_status = "INCOMPLET"
    return {
        "schema": "rcs70_diffusion_proof/v1",
        "issue": ISSUE,
        "script": SCRIPT_REL.as_posix(),
        "artefact": artifact_info,
        "preuves": evidence,
        "metriques_synthetiques": metrics,
        "checks": checks,
        "proof_status": proof_status,
        "decision": "A_TESTER",
        "medical_claim": False,
        "clinical_validation": False,
        "blocking_reasons": [
            "Jeu C3 non gelé collectivement (RCS-69/RCS-81) : aucune comparaison validée.",
            "Source de données autorisée et licence à vérifier avant tout transfert.",
            "Le démonstrateur porte sur des signaux synthétiques, sans dispositif ni patient.",
            "Artefact d'exécution à fournir par un humain : aucun résultat n'est généré ici.",
        ],
        "note": (
            "Contrôles structurels uniquement : le schéma strict rejette les clés inattendues "
            "et les marqueurs sensibles imbriqués, mais le hash du fichier ne prouve ni son "
            "exécution, ni l'authenticité de l'expérience, ni une validation clinique."
        ),
    }


def serialize(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_doc(report: Dict[str, Any]) -> str:
    lines = [
        f"# {ISSUE} — Manifeste de diffusion (contrôles structurels)",
        "",
        "> Décision : **A_TESTER**. Les indices textuels ne prouvent pas un entraînement ; "
        "les artefacts fournis restent des déclarations non authentifiées.",
        "",
        "## Chaîne à vérifier par exécution",
        "",
        "- `q_sample` / bruit gaussien puis prédiction de `epsilon` par un MLP entraîné ;",
        "- échantillonneur inverse DDPM (`sample`) à exécuter ;",
        "- seuil fixé sur validation indépendante, détection comparée à une baseline MAD ;",
        "- seed, versions, hash du jeu et temps d'entraînement consignés dans l'artefact si fourni.",
        "",
        "## Preuves (ND tant qu'un artefact réel n'est pas fourni)",
        "",
        "| Champ | Valeur |",
        "|---|---|",
    ]
    for key, value in report["preuves"].items():
        lines.append(f"| {key} | {value} |")
    lines += ["", "| Métrique synthétique (uniquement si artefact fourni) | Valeur |", "|---|---|"]
    for key, value in report["metriques_synthetiques"].items():
        lines.append(f"| {key} | {value} |")
    lines += ["", "## Contrôles", "", "| Contrôle | Résultat |", "|---|---|"]
    for key, value in report["checks"].items():
        lines.append(f"| {key} | {'OK' if value else 'ÉCHEC / ND'} |")
    lines += [
        "",
        f"**Statut de preuve : {report['proof_status']} — décision : {report['decision']}.**",
        "",
        "## Bloquants avant clôture du ticket",
        "",
    ]
    lines += [f"- {reason}" for reason in report["blocking_reasons"]]
    lines += [
        "",
        "## Reproduction",
        "",
        "```bash",
        "python -m tools.rcs70_diffusion_proof --write",
        "python -m tools.rcs70_diffusion_proof --artifact <artefact.json> --write",
        "python -m tools.rcs70_diffusion_proof --check",
        "python -m experiments.rcs69_diffusion_numpy --seed 42 --updates 250 --json <artefact.json>",
        "python -m unittest tests.test_rcs70_diffusion_proof -v",
        "```",
        "",
        "Références : PR #7 (`ccabf36`), `docs/19_rcs69_diffusion_numpy_poc.md`, "
        "`docs/16_rcs69_preparation_preuve_c3.md`, ADR-008, tickets RCS-69/RCS-70/RCS-81.",
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
    if not report["checks"]["structure_textuelle_presente"]:
        reasons.append("structure textuelle de débruitage absente")
    if not report["checks"]["schema_artefact_strict"]:
        reasons.append("schéma d'artefact non strict : clé inattendue ou donnée sensible détectée")
    if report["medical_claim"] or report["clinical_validation"]:
        reasons.append("aucune revendication médicale n'est autorisée")
    if report["decision"] != "A_TESTER":
        reasons.append("décision A_TESTER exigée tant que les cas ne sont pas gelés")
    return not reasons, reasons


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RCS-70 — manifeste de preuve diffusion")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--artifact")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.root, args.artifact)
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
