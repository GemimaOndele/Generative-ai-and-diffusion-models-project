"""Comparaison structurée des approches — RCS-22. Sans résultat chiffré."""
from __future__ import annotations
import re
import sys
from dataclasses import dataclass

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
    Approach("A", "Statu quo (manuel)", "Expertise et seuils fixes", "Procédures", "Bon sur cas connus", "Faible", "Faible", "Élevé", "Variable", "Élevée", "Oubli, charge", "Élevée", "Retours terrain"),
    Approach("B", "Règles / ML classique", "Règles et modèles supervisés", "Dataset étiqueté", "Bonne baseline", "Moyenne", "Moyen", "Faible à moyen", "Faible", "Moyenne à élevée", "Biais, dérive", "Élevée", "Notebook reproductible"),
    Approach("C", "Diffusion / GenAI (J1)", "Apprentissage de la distribution", "Séries temporelles", "À prouver", "Potentielle", "Moyen à élevé", "Moyen à élevé", "Moyenne à élevée", "Plus faible", "Artefacts", "Moyenne", "Cas figés, seed, logs"),
    Approach("V2", "Routage multi-LLM (non validé)", "Routage + repli cascade", "Cas figés, A/B validés", "À mesurer", "À mesurer", "Moyen", "À mesurer", "À mesurer", "Traces requises", "Supériorité non démontrée", "Démo seule", "RCS-75"),
)

@dataclass(frozen=True)
class Hypothesis:
    id: str
    statement: str
    falsifier: str

HYPOTHESES = (
    Hypothesis("H1", "Le règles/ML dépasse le statu quo sur cas figés.", "F1 non supérieur ou faux négatifs hors seuil."),
    Hypothesis("H2", "La diffusion apporte un gain mesurable.", "Absence de gain ou dépassement coût/latence."),
    Hypothesis("H3", "Sans gain, le règles/ML reste la référence.", "Preuve contraire sur cas figés."),
    Hypothesis("H4", "Le routage réduit le coût sans perte de qualité.", "Absence de réduction de coût ou perte qualité."),
)

@dataclass(frozen=True)
class ProtocolAxis:
    axis: str
    metric: str
    status: str
    source: str

PROTOCOL = (
    ProtocolAxis("Qualité", "Rappel, précision, F1", "ND", "docs/05_tp04_benchmark.md"),
    ProtocolAxis("Diversité", "Couverture des cas", "ND", "RCS-79"),
    ProtocolAxis("Coût", "Coût par cas réussi", "ND", "src/orchestrator.py"),
    ProtocolAxis("Limites", "Cas d'échec", "ND", "RCS-18, RCS-88"),
    ProtocolAxis("Faisabilité", "Environnement, données", "ND", "RCS-56/57/70"),
)

def provisional_choice():
    return {
        "reference": "B. règles / ML",
        "research": "C. diffusion en POC cadré",
        "optimization": "V2 routage multi-LLM, à mesurer",
        "status": "provisoire — GO/NO-GO après benchmark RCS-81",
        "rationale": "Hypothèses réfutables, reproductibilité, H3",
    }

def validate_no_results():
    errors = []
    for axis in PROTOCOL:
        if axis.status != "ND":
            errors.append(f"{axis.axis}: statut {axis.status} devrait être ND")
    for approach in APPROACHES:
        for field in ("quality", "diversity", "cost_initial", "cost_ops", "latency"):
            if re.search(r"\b\d+(?:\.\d+)?\s*%|\bF1\s*=\s*\d", getattr(approach, field)):
                errors.append(f"{approach.id}.{field}: mesure chiffrée non autorisée")
    for hypothesis in HYPOTHESES:
        if not hypothesis.falsifier:
            errors.append(f"{hypothesis.id}: réfutation manquante")
    return errors

def render_comparison_table():
    lines = ["| ID | Approche | Qualité | Diversité | Coût initial | Faisabilité | Preuve |", "|---|---|---|---|---|---|---|"]
    for a in APPROACHES:
        lines.append(f"| {a.id} | {a.name} | {a.quality} | {a.diversity} | {a.cost_initial} | {a.feasibility} | {a.evidence} |")
    return "\n".join(lines)

def main(argv=None):
    errors = validate_no_results()
    if errors:
        for error in errors:
            print("ERREUR:", error)
        return 1
    print(f"Comparaison RCS-22 — {len(APPROACHES)} approches, {len(HYPOTHESES)} hypothèses.")
    print("Choix provisoire :", provisional_choice()["status"])
    print(render_comparison_table())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())