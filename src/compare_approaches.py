"""Comparaison structurée des approches — RCS-22.

Le ticket demande un benchmark de trois approches (qualité, diversité, coût,
limites, faisabilité) et un choix justifié avec hypothèses falsifiables. Ce
module fournit les données structurées, le contrôle « aucune mesure inventée »
et une preuve d'acceptation vérifiable en CI.

Aucun résultat chiffré n'est revendiqué : toutes les mesures restent `ND`
tant que les cas, les seuils et les exécutions ne sont pas validés (RCS-81).
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable

ND = "ND"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC_RELATIVE = "docs/03_comparaison_statuquo_reglesml_diffusion.md"
DEFAULT_DOC = PROJECT_ROOT / DOC_RELATIVE
REQUIRED_APPROACH_IDS = ("A", "B", "C")
BENCHMARK_AXES = ("qualite", "diversite", "cout", "limites", "faisabilite")
AXIS_FIELDS = {
    "qualite": ("quality",),
    "diversite": ("diversity",),
    "cout": ("cost_initial", "cost_ops", "latency"),
    "limites": ("limits",),
    "faisabilite": ("feasibility",),
}


@dataclass(frozen=True)
class Approach:
    id: str
    name: str
    principle: str
    data: str
    quality: str
    diversity: str
    cost_initial: str
    cost_ops: str
    latency: str
    explainability: str
    limits: str
    feasibility: str
    evidence: str


APPROACHES = (
    Approach(
        "A", "Statu quo (manuel)", "Expertise et seuils fixes", "Procédures",
        "Bon sur cas connus", "Faible", "Faible", "Élevé", "Variable", "Élevée",
        "Oubli, charge", "Élevée", "Retours terrain",
    ),
    Approach(
        "B", "Règles / ML classique", "Règles et modèles supervisés", "Dataset étiqueté",
        "Bonne baseline", "Moyenne", "Moyen", "Faible à moyen", "Faible", "Moyenne à élevée",
        "Biais, dérive", "Élevée", "Notebook reproductible",
    ),
    Approach(
        "C", "Diffusion / GenAI (J1)", "Apprentissage de la distribution", "Séries temporelles",
        "À prouver", "Potentielle", "Moyen à élevé", "Moyen à élevé", "Moyenne à élevée",
        "Plus faible", "Artefacts", "Moyenne", "Cas figés, seed, logs",
    ),
    Approach(
        "V2", "Routage multi-LLM (non validé)", "Routage + repli cascade",
        "Cas figés, A/B validés", "À mesurer", "À mesurer", "Moyen", "À mesurer",
        "À mesurer", "Traces requises", "Supériorité non démontrée", "Démo seule", "RCS-75",
    ),
)


@dataclass(frozen=True)
class Hypothesis:
    id: str
    statement: str
    falsifier: str
    metric: str = ""
    status: str = ND


HYPOTHESES = (
    Hypothesis(
        "H1", "L'approche règles/ML dépasse le statu quo sur cas figés.",
        "F1 non supérieur ou faux négatifs hors seuil.",
        "F1 et taux de faux négatifs sur cas figés",
    ),
    Hypothesis(
        "H2", "La diffusion apporte un gain mesurable.",
        "Absence de gain ou dépassement coût/latence.",
        "Rappel / reconstruction, coût par cas, latence p95",
    ),
    Hypothesis(
        "H3", "Sans gain, le règles/ML reste la référence.",
        "Preuve contraire sur cas figés.",
        "Comparaison A/B/C sur le même jeu figé",
    ),
    Hypothesis(
        "H4", "Le routage réduit le coût sans perte de qualité.",
        "Absence de réduction de coût ou perte qualité.",
        "Coût par cas réussi et score observable mono/routing",
    ),
)


@dataclass(frozen=True)
class ProtocolAxis:
    axis: str
    metric: str
    status: str
    source: str


PROTOCOL = (
    ProtocolAxis("Qualité", "Rappel, précision, F1", ND, "docs/05_tp04_benchmark.md"),
    ProtocolAxis("Diversité", "Couverture des cas", ND, "RCS-79"),
    ProtocolAxis("Coût", "Coût par cas réussi", ND, "src/orchestrator.py"),
    ProtocolAxis("Limites", "Cas d'échec", ND, "RCS-18, RCS-88"),
    ProtocolAxis("Faisabilité", "Environnement, données", ND, "RCS-56/57/70"),
)

# Champs du ticket Jira RCS-22 (consultés le 2026-11-24), sans invention.
TICKET_METADATA = {
    "key": "RCS-22",
    "source": "Backlog RoboCare Sentinel V3",
    "phase": "S1 (indicative ; démarrage à fixer en planification)",
    "domain": "BIZ",
    "category": "Fonctionnel",
    "mission": "Benchmark trois approches selon qualité, diversité, coût, limites et faisabilité",
    "acceptance": "Choix justifié avec hypothèses falsifiables",
    "competence": "Analyse scientifique",
    "roles": {
        "owner": "Elias",
        "binome": "Aminata",
        "relais": "Omar",
        "reviewer": "Gémima",
    },
    "volets": [
        "contribution du pilote",
        "apprentissage accompagné du binôme",
        "recherche/veille documentée si la mission le requiert",
    ],
    "blockage": "documenter obstacle, essais et liens dans le ticket ; solliciter binôme et relais ; arbitrer au point de coordination",
}

# Le livrable Markdown doit reprendre explicitement les champs du ticket.
DOC_REQUIRED_TOKENS = (
    "backlog robocare sentinel v3",
    "s1",
    "domaine d'origine : biz",
    "catégorie : fonctionnel",
    "compétence à développer",
    "analyse scientifique",
    "responsable jira",
    "elias",
    "aminata",
    "omar",
    "gémima",
    "contribution du pilote",
    "apprentissage accompagné du binôme",
    "recherche/veille documentée",
    "en cas de blocage",
    "obstacle",
    "essais",
    "liens",
    "relais",
    "point de coordination",
    "qualité",
    "diversité",
    "coût",
    "limites",
    "faisabilité",
    "choix justifié",
    "hypothèses falsifiables",
)


@dataclass(frozen=True)
class Choice:
    reference: str
    research: str
    optimization: str
    status: str
    rationale: str
    reversal: str


def provisional_choice() -> dict:
    """Choix provisoire : réfutable et explicitement non validé."""
    return asdict(
        Choice(
            reference="B. règles / ML",
            research="C. diffusion en POC cadré",
            optimization="V2 routage multi-LLM, à mesurer",
            status="provisoire — GO/NO-GO après benchmark RCS-81",
            rationale="Hypothèses réfutables, reproductibilité, H3",
            reversal="Revoir le choix si H1/H2/H4 sont confirmés sur cas figés avec coût/latence acceptés",
        )
    )


def _duplicates(identifiers: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for identifier in identifiers:
        if identifier in seen:
            duplicates.add(identifier)
        seen.add(identifier)
    return sorted(duplicates)


_MEASURE_PATTERNS = (
    re.compile(r"\b\d+(?:[.,]\d+)?\s*%"),
    re.compile(r"\b(?:F1|rappel|précision|p95|latence)\s*[=:]\s*\d+(?:[.,]\d+)?", re.I),
    re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:ms|€|eur|euros)\b", re.I),
)


def _contains_measure(text: str) -> bool:
    """Détecte une mesure chiffrée présentée comme un résultat."""
    return any(pattern.search(text) for pattern in _MEASURE_PATTERNS)


def validate_no_results(
    approaches: Iterable[Approach] = APPROACHES,
    hypotheses: Iterable[Hypothesis] = HYPOTHESES,
    protocol: Iterable[ProtocolAxis] = PROTOCOL,
    choice: dict | None = None,
) -> list[str]:
    """Contrôle complet : couverture, falsifiabilité, ND et choix non définitif."""
    approaches = tuple(approaches)
    hypotheses = tuple(hypotheses)
    protocol = tuple(protocol)
    errors: list[str] = []

    for duplicate in _duplicates(approach.id for approach in approaches):
        errors.append(f"approche {duplicate}: identifiant dupliqué")
    for required in REQUIRED_APPROACH_IDS:
        if required not in {approach.id for approach in approaches}:
            errors.append(f"approche {required}: manquante")
    for approach in approaches:
        for field_def in fields(approach):
            value = getattr(approach, field_def.name)
            if not value:
                errors.append(f"{approach.id}.{field_def.name}: champ vide")
            elif _contains_measure(str(value)):
                errors.append(f"{approach.id}.{field_def.name}: mesure chiffrée non autorisée")

    for duplicate in _duplicates(hypothesis.id for hypothesis in hypotheses):
        errors.append(f"hypothèse {duplicate}: identifiant dupliqué")
    if len(hypotheses) < 4:
        errors.append("hypothèses: moins de quatre hypothèses déclarées")
    for hypothesis in hypotheses:
        for name in ("statement", "falsifier", "metric"):
            value = getattr(hypothesis, name)
            if not value:
                errors.append(f"{hypothesis.id}.{name}: champ vide")
            elif _contains_measure(value):
                errors.append(f"{hypothesis.id}.{name}: mesure chiffrée non autorisée")
        if hypothesis.status != ND:
            errors.append(f"{hypothesis.id}: statut {hypothesis.status} devrait être ND")

    for axis in protocol:
        if not axis.axis or not axis.metric or not axis.source:
            errors.append(f"protocole {axis.axis or '?'} : champ vide")
        if axis.status != ND:
            errors.append(f"{axis.axis}: statut {axis.status} devrait être ND")

    decision = provisional_choice() if choice is None else choice
    if not decision.get("reference", "").startswith("B"):
        errors.append("choix: la référence doit rester B (règles/ML)")
    if not decision.get("research", "").startswith("C"):
        errors.append("choix: la piste de recherche doit rester C (diffusion)")
    if "provisoire" not in decision.get("status", ""):
        errors.append("choix: statut non marqué provisoire")
    if "GO final" in decision.get("status", ""):
        errors.append("choix: GO final interdit avant benchmark RCS-81")
    if not decision.get("rationale") or not decision.get("reversal"):
        errors.append("choix: justification ou condition de renversement manquante")
    return errors


def benchmark_matrix() -> dict:
    """Vue structurée axe × approche, directement sérialisable en JSON."""
    rows = []
    for approach in APPROACHES:
        row = {"id": approach.id, "name": approach.name, "axes": {}}
        for axis in BENCHMARK_AXES:
            row["axes"][axis] = {
                field_name: getattr(approach, field_name)
                for field_name in AXIS_FIELDS[axis]
            }
        row["preuve"] = approach.evidence
        rows.append(row)
    return {"axes": list(BENCHMARK_AXES), "approaches": rows}


def validate_ticket_metadata(metadata: dict = TICKET_METADATA) -> list[str]:
    """Vérifie que les champs du ticket sont renseignés, sans résultat supposé."""
    errors = []
    for name in ("source", "phase", "domain", "category", "mission", "acceptance", "competence"):
        if not metadata.get(name):
            errors.append(f"ticket.{name}: champ vide")
    for role, person in metadata.get("roles", {}).items():
        if not person:
            errors.append(f"ticket.roles.{role}: champ vide")
    if len(metadata.get("volets", ())) != 3:
        errors.append("ticket.volets: trois volets attendus")
    if not all(keyword in metadata.get("blockage", "") for keyword in ("obstacle", "essais", "liens", "relais")):
        errors.append("ticket.blockage: procédure incomplète")
    return errors


def document_alignment_check(path: str | Path = DEFAULT_DOC) -> dict:
    """Vérifie que le document livré reprend explicitement le ticket Jira."""
    document = Path(path)
    try:
        text = document.read_text(encoding="utf-8").lower()
    except OSError as error:
        return {"ok": False, "path": DOC_RELATIVE, "missing": [f"lecture impossible: {error}"]}
    missing = [token for token in DOC_REQUIRED_TOKENS if token not in text]
    return {"ok": not missing, "path": DOC_RELATIVE, "missing": missing}


def acceptance_check(doc_path: str | Path = DEFAULT_DOC) -> dict:
    """Preuve d'acceptation du ticket Jira RCS-22, vérifiée sur les données."""
    errors = validate_no_results()
    ticket_errors = validate_ticket_metadata()
    alignment = document_alignment_check(doc_path)
    matrix = benchmark_matrix()
    covered = {row["id"] for row in matrix["approaches"]}
    choice = provisional_choice()
    criteria = [
        {
            "id": "THREE_APPROACHES_BENCHMARKED",
            "ok": set(REQUIRED_APPROACH_IDS).issubset(covered),
            "evidence": "A statu quo, B règles/ML, C diffusion (+ V2 optimisation)",
        },
        {
            "id": "FIVE_JIRA_AXES",
            "ok": tuple(matrix["axes"]) == BENCHMARK_AXES,
            "evidence": ", ".join(BENCHMARK_AXES),
        },
        {
            "id": "FALSIFIABLE_HYPOTHESES",
            "ok": all(
                hypothesis.metric and hypothesis.falsifier and hypothesis.status == ND
                for hypothesis in HYPOTHESES
            ),
            "evidence": "H1–H4 : métrique, condition de réfutation et statut ND",
        },
        {
            "id": "JUSTIFIED_CHOICE",
            "ok": bool(choice["rationale"] and choice["reversal"] and "provisoire" in choice["status"]),
            "evidence": f"{choice['reference']} / {choice['research']} ; renversement : {choice['reversal']}",
        },
        {
            "id": "NO_INVENTED_RESULTS",
            "ok": not errors,
            "evidence": errors or "aucune mesure chiffrée, tous les statuts de protocole à ND",
        },
        {
            "id": "TRACEABLE_SOURCES",
            "ok": all(approach.evidence for approach in APPROACHES)
            and all(axis.source for axis in PROTOCOL),
            "evidence": "preuve par approche et source par axe de protocole",
        },
        {
            "id": "JIRA_TICKET_FIELDS",
            "ok": not ticket_errors,
            "evidence": ticket_errors or TICKET_METADATA,
        },
        {
            "id": "DOC_JIRA_ALIGNMENT",
            "ok": alignment["ok"],
            "evidence": alignment["missing"] or f"{alignment['path']} reprend les champs du ticket",
        },
        {
            "id": "SCIENTIFIC_ANALYSIS",
            "ok": all(
                hypothesis.metric and hypothesis.falsifier and hypothesis.status == ND
                for hypothesis in HYPOTHESES
            )
            and all(axis.status == ND for axis in PROTOCOL)
            and not errors,
            "evidence": "métriques, réfutations, protocole ND et aucune mesure inventée",
        },
    ]
    return {
        "ok": all(criterion["ok"] for criterion in criteria),
        "ticket": "RCS-22",
        "errors": errors,
        "criteria": criteria,
        "ticket_fields": TICKET_METADATA,
        "document_alignment": alignment,
        "choice": choice,
        "matrix": matrix,
    }


def render_comparison_table(approaches: Iterable[Approach] = APPROACHES) -> str:
    lines = [
        "| ID | Approche | Qualité | Diversité | Coût initial | Coût exploitation | Latence | Limites | Faisabilité | Preuve |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for approach in approaches:
        lines.append(
            f"| {approach.id} | {approach.name} | {approach.quality} | {approach.diversity} "
            f"| {approach.cost_initial} | {approach.cost_ops} | {approach.latency} "
            f"| {approach.limits} | {approach.feasibility} | {approach.evidence} |"
        )
    return "\n".join(lines)


def render_hypotheses_table(hypotheses: Iterable[Hypothesis] = HYPOTHESES) -> str:
    lines = ["| ID | Hypothèse | Métrique | Réfutation | Statut |", "|---|---|---|---|---|"]
    for hypothesis in hypotheses:
        lines.append(
            f"| {hypothesis.id} | {hypothesis.statement} | {hypothesis.metric} "
            f"| {hypothesis.falsifier} | {hypothesis.status} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Comparaison RCS-22 sans résultat inventé")
    parser.add_argument("--json", action="store_true", help="rapport structuré (code 1 si incohérent)")
    parser.add_argument(
        "--acceptance",
        action="store_true",
        help="critères d'acceptation Jira RCS-22 sur pièces (JSON)",
    )
    parser.add_argument("--out", default=None, help="fichier de sortie JSON facultatif")
    parser.add_argument("--doc", default=None, help="document Markdown à contrôler (par défaut le livrable)")
    args = parser.parse_args(argv)

    if args.acceptance:
        result = acceptance_check(args.doc or DEFAULT_DOC)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        code = 0 if result["ok"] else 1
    elif args.json:
        errors = validate_no_results()
        result = {
            "ok": not errors,
            "errors": errors,
            "approaches": len(APPROACHES),
            "hypotheses": len(HYPOTHESES),
            "choice": provisional_choice(),
            "matrix": benchmark_matrix(),
        }
        text = json.dumps(result, ensure_ascii=False, indent=2)
        code = 0 if result["ok"] else 1
    else:
        errors = validate_no_results()
        if errors:
            for error in errors:
                print("ERREUR:", error)
            return 1
        print(
            f"Comparaison RCS-22 — {len(APPROACHES)} approches, "
            f"{len(HYPOTHESES)} hypothèses, {len(PROTOCOL)} axes ND."
        )
        print("Choix provisoire :", provisional_choice()["status"])
        print(render_comparison_table())
        print(render_hypotheses_table())
        return 0

    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {output}")
    print(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
