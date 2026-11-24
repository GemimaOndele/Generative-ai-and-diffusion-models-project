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
FORBIDDEN_KEYS = ("patient", "diagnostic", "identifier", "nom", "surname")


def structure_checks(source: str) -> Dict[str, bool]:
    """Différencie un débruiteur entraîné d'un simple bruitage."""
    lowered = source.lower()
    return {
        "denoiser_entraine": "denoiser" in lowered and "def train(" in lowered and "epsilon" in lowered,
        "echantillonneur_inverse": "def sample(" in lowered and "reverse" in lowered and "ddpm" in lowered,
        "seed_explicite": "seed" in lowered,
        "pas_simple_bruitage": "learned" in lowered and "reverse" in lowered,
    }


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
            if key in payload:
                evidence[key] = payload[key]
        for key in METRIC_KEYS:
            if key in payload:
                metrics[key] = payload[key]

    forbidden = [
        key for key in evidence if any(marker in key.lower() for marker in FORBIDDEN_KEYS)
    ]
    checks.update({
        "code_debruitage_reel": all(structure_checks(source).values()),
        "artefact_present": artifact_info["present"],
        "artefact_complet": artifact_info["present"] and all(
            evidence[key] not in (ND, None, "") for key in EVIDENCE_KEYS
        ),
        "perimetre_synthetique_declare": str(evidence["scope"]).startswith("synthetic")
        and "not_clinical" in str(evidence["scientific_status"]),
        "sans_donnees_patient": not forbidden and "patient" not in json.dumps(metrics, ensure_ascii=False).lower(),
    })
    if not checks["code_debruitage_reel"]:
        proof_status = "BLOQUE"
    elif not artifact_info["present"]:
        proof_status = "ND"
    elif all(checks.values()):
        proof_status = "DEMO_SYNTHETIQUE"
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
        "note": "Code de débruitage réel ne signifie pas preuve clinique ni transfert médical.",
    }


def serialize(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_doc(report: Dict[str, Any]) -> str:
    lines = [
        f"# {ISSUE} — Preuve de diffusion réelle (débruitage, pas simple bruitage)",
        "",
        "> Décision : **A_TESTER**. Le code vérifie un débruiteur DDPM entraîné "
        "sur signaux synthétiques ; aucune mesure clinique ni artifact fabriqué "
        "n'est revendiqué ici.",
        "",
        "## Chaîne minimale vérifiée",
        "",
        "- `q_sample` / bruit gaussien puis prédiction de `epsilon` par un MLP entraîné ;",
        "- échantillonneur inverse DDPM (`sample`) réellement exécuté ;",
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
    if not report["checks"]["code_debruitage_reel"]:
        reasons.append("code de débruitage non vérifié")
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
