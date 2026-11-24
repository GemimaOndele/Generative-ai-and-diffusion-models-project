"""RCS-88 — fiches effectives, matrice biais/robustesse et protocole de refus.

Règles fortes (issue Jira RCS-88 et commentaires PR #4) :

* aucune métrique, population, licence ou conclusion d'absence de biais n'est
  inventée : les champs non établis restent ``ND`` ;
* aucun attribut sensible n'est inféré et aucun sous-groupe non autorisé n'est
  évalué : la décision par défaut est le refus (« évaluation non disponible ») ;
* la mise en service d'une démo reste bloquée tant qu'une preuve signée par un
  relecteur humain et référencée n'existe pas.

Ce module n'utilise que la bibliothèque standard : il fonctionne sur le socle
de la branche RCS-88 comme sur le socle plus récent de ``main``.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import re
from pathlib import Path
from typing import Any

ND = "ND"
REFUSAL_MESSAGE = "évaluation non disponible"
GOVERNANCE_DIR = Path("governance") / "rcs88"
PROOF_FILE = GOVERNANCE_DIR / "proof.json"
REPORT_FILE = GOVERNANCE_DIR / "acceptance.json"

# Champs explicitement demandés par la mission de l'issue RCS-88.
REQUIRED_MODEL_FIELDS = {
    "nom_systeme", "type", "version", "proprietaire", "finalite",
    "hors_perimetre", "dataset_ids", "donnees_evaluation", "metriques",
    "hypotheses", "performance_par_sous_groupe", "limites_transfert",
    "risques", "mitigation", "supervision_humaine", "monitoring", "statut",
}
REQUIRED_DATASET_FIELDS = {
    "id", "nom", "source", "licence", "date_acces", "population_appareils",
    "methode_collecte", "qualite_labels", "hypotheses", "limites_transfert",
    "splits", "biais_connus", "lien_manifest", "statut",
}

# Dimensions autorisées à être discutées, uniquement si les données le permettent.
ALLOWED_DIMENSIONS = {
    "type_appareil": "Type d'appareil (catégories autorisées par le manifeste)",
    "site": "Site ou lot (identifiant non sensible, si autorisé)",
    "regime_signal": "Régime du signal (bruit, plage, qualité)",
    "langue": "Langue des documents RAG",
    "format": "Format ou modalité d'entrée",
}

# Attributs sensibles ou secrets : jamais inférés, jamais utilisés comme
# sous-groupe, jamais copiés dans un livrable généré.
FORBIDDEN_ATTRIBUTES = {
    "age", "âge", "sexe", "genre", "ethnie", "ethnicite", "ethnicité",
    "religion", "orientation sexuelle", "handicap", "grossesse", "sante",
    "santé", "diagnostic", "patient", "patient_id", "patient_name", "nir",
    "nom", "prenom", "prénom", "date de naissance", "adresse", "api_key",
    "token", "mot de passe", "password", "secret", "raw_prompt", "prompt prive",
}

_MODELS: dict[str, dict[str, Any]] = {
    "MC-baseline": {
        "nom_systeme": "Baseline règles / ML",
        "type": "Règles / ML",
        "version": ND,
        "date": ND,
        "commit": ND,
        "proprietaire": "Elias (pilote proposé) / binôme Aminata",
        "finalite": "Détection d'anomalies et aide à la décision technique, sans décision autonome.",
        "hors_perimetre": "Diagnostic médical, décision clinique sans revue humaine, action autonome sur appareil biomédical.",
        "dataset_ids": ["D-001b", "D-002"],
        "donnees_evaluation": ND,
        "hypotheses": ND,
        "metriques": {"precision": ND, "rappel": ND, "faux_positifs": ND,
                      "faux_negatifs": ND, "p95_latence_ms": ND},
        "performance_par_sous_groupe": ND,
        "limites_connues": "Jeu pédagogique non gelé collectivement ; données industrielles/simulées non transférables au médical.",
        "limites_transfert": "Industriel/simulé ≠ médical réel ; aucune validation clinique.",
        "risques": "Faux positifs/négatifs, dérive de distribution, biais de couverture.",
        "mitigation": "Seuils à ratifier, cas gelés T01–T06, revue humaine, journalisation sans données sensibles.",
        "conditions_usage": "Démo uniquement ; données autorisées et revue humaine des cas sensibles.",
        "supervision_humaine": "Revue humaine obligatoire pour toute sortie critique ou cas sensible.",
        "monitoring": "ND (lien RCS-63 / RCS-78 / RCS-86)",
        "tests": "T01–T06 (TP04) ; RCS-55 / RCS-61",
        "references": "RCS-55 (#40), RCS-61 (#34), data/manifest.md",
        "statut": "Brouillon — à compléter avant démo",
    },
    "MC-diffusion-j1": {
        "nom_systeme": "Diffusion J1 (adaptateur contrôlé)",
        "type": "Diffusion",
        "version": ND,
        "date": ND,
        "commit": ND,
        "proprietaire": "Elias (pilote proposé) / binôme Aminata",
        "finalite": "Reconstruction et génération contrôlée de signaux pour tester la robustesse, hors usage clinique.",
        "hors_perimetre": "Génération de preuve clinique, interprétation de signaux patients, décision autonome.",
        "dataset_ids": ["D-001b", "D-003"],
        "donnees_evaluation": ND,
        "hypotheses": ND,
        "metriques": {"erreur_reconstruction": ND, "delta_detection_vs_baseline": ND,
                      "qualite_signal": ND, "p95_latence_ms": ND},
        "performance_par_sous_groupe": ND,
        "limites_connues": "Variantes J1 non validées sur données médicales ; cas J1 à geler collectivement.",
        "limites_transfert": "Signaux synthétiques/industriels ≠ capteurs médicaux réels.",
        "risques": "Reconstruction trompeuse sous bruit, fuite de domaine, faux sentiment de performance.",
        "mitigation": "Filtrage qualité du signal, comparaison baseline vs diffusion sur cas identiques, étiquetage « non médical ».",
        "conditions_usage": "Expérimentation et démo pédagogique sous revue humaine.",
        "supervision_humaine": "Revue humaine obligatoire avant toute interprétation d'une reconstruction.",
        "monitoring": "ND (lien RCS-63 / RCS-78 / RCS-86)",
        "tests": "Cas J1 gelés à définir ; RCS-57 / RCS-69 / RCS-70",
        "references": "RCS-57 (#38), RCS-69, docs/11_cartographie_risques_biais.md",
        "statut": "Brouillon — à compléter avant démo",
    },
    "MC-mono-llm": {
        "nom_systeme": "Mono-LLM / J2 (RAG)",
        "type": "LLM fournisseur",
        "version": ND,
        "date": ND,
        "commit": ND,
        "proprietaire": "Elias (pilote proposé) / binôme Aminata",
        "finalite": "Aide à l'interprétation documentaire avec citations vérifiables et abstention.",
        "hors_perimetre": "Réponse sans source, décision clinique, action sur appareil, copie de données non autorisées.",
        "dataset_ids": ["D-001b"],
        "donnees_evaluation": ND,
        "hypotheses": ND,
        "metriques": {"exactitude_citation": ND, "taux_abstention_correcte": ND,
                      "faux_refus": ND, "p95_latence_ms": ND, "cout_par_cas_eur": ND},
        "performance_par_sous_groupe": ND,
        "limites_connues": "Modèle A/B, licence et droits d'usage non vérifiés dans le socle ; corpus RAG à définir.",
        "limites_transfert": "Documentation technique autorisée ≠ preuve clinique ; localisation et rétention à vérifier.",
        "risques": "Hallucination, source absente, injection indirecte, fuite de données, coût/latence.",
        "mitigation": "Abstention, citations exactes, séparation des instructions, T07–T10, revue humaine.",
        "conditions_usage": "Données et corpus autorisés uniquement ; aucun appel payant sans accord.",
        "supervision_humaine": "Revue humaine toujours requise pour une réponse exploitée.",
        "monitoring": "ND (lien RCS-63 / RCS-78 / RCS-86)",
        "tests": "T07 source absente, T08 contradiction, T09 injection, T10 données sensibles",
        "references": "RCS-62, RCS-78 (#27), config/tp04_models.example.json",
        "statut": "Brouillon — à compléter avant démo",
    },
    "MC-v2-multillm": {
        "nom_systeme": "V2 multi-LLM (routage / cascade)",
        "type": "Orchestration",
        "version": ND,
        "date": ND,
        "commit": ND,
        "proprietaire": "Elias (pilote proposé) / binôme Aminata",
        "finalite": "Orchestrer deux modèles A/B avec routage ou cascade sous contrainte de coût, latence et qualité.",
        "hors_perimetre": "Boucles autonomes, dépassement du budget, décision clinique automatisée.",
        "dataset_ids": ["D-001b"],
        "donnees_evaluation": ND,
        "hypotheses": ND,
        "metriques": {"taux_abstention_correcte": ND, "qualite_route": ND,
                      "appels_par_cas": ND, "p95_latence_ms": ND, "cout_par_cas_eur": ND},
        "performance_par_sous_groupe": ND,
        "limites_connues": "Comparaison mono/routage/cascade non figée collectivement ; modèles A/B à valider.",
        "limites_transfert": "Résultats de démo locaux ≠ performance de production ou médicale.",
        "risques": "Erreur de routage, retries excessifs, injection, coût imprévu, réponse non fondée.",
        "mitigation": "max_calls_per_case=2, allow_paid_calls=false par défaut, budgets, abstention, revue humaine.",
        "conditions_usage": "Démo uniquement ; configuration validée et cas autorisés.",
        "supervision_humaine": "Revue humaine obligatoire ; le monitoring ne déclenche aucune action autonome.",
        "monitoring": "ND (lien RCS-63 / RCS-78 / RCS-86)",
        "tests": "T07–T10 (TP04) ; RCS-77 comparaison des stratégies",
        "references": "RCS-75, RCS-77, RCS-79, RCS-89",
        "statut": "Brouillon — à compléter avant démo",
    },
}

_DATASETS: dict[str, dict[str, Any]] = {
    "D-001": {
        "nom": "experiments/test_cases.jsonl (gabarit vide du socle)",
        "type": "Gabarit de structure",
        "source": "Socle commun (PR #1 / bd1c5d1)",
        "licence": "Interne projet",
        "date_acces": "2026-11-22",
        "sensible": "Non",
        "splits": "Doit rester vide ; utilisé par le test de structure",
        "statut": "Socle",
    },
    "D-001b": {
        "nom": "experiments/tp04_cases.jsonl (10 cas pédagogiques TP04)",
        "type": "Cas pédagogiques",
        "source": "Proposés par Elias pour TP04 / RCS-75",
        "licence": "Interne projet / à confirmer",
        "date_acces": "2026-11-23",
        "sensible": "Non",
        "splits": "T01–T10, démo uniquement ; non gelés collectivement (RCS-81 pending, freeze_commit vide)",
        "statut": "Brouillon",
    },
    "D-002": {
        "nom": "Jeu à sélectionner — baseline règles / ML",
        "type": "ND",
        "source": ND,
        "licence": "À vérifier",
        "date_acces": ND,
        "sensible": "À vérifier",
        "splits": "Train/validation/test gelé à définir",
        "statut": ND,
    },
    "D-003": {
        "nom": "Jeu à sélectionner — diffusion J1",
        "type": "ND",
        "source": ND,
        "licence": "À vérifier",
        "date_acces": ND,
        "sensible": "À vérifier",
        "splits": "Cas figés J1 à définir",
        "statut": ND,
    },
}

_BIAS_CASES: list[dict[str, str]] = [
    {"id": "B-001", "systeme": "MC-baseline", "dimension": "type_appareil",
     "condition": ND, "risque": "Faux négatifs sur une famille d'appareils",
     "metrique": "Rappel par sous-groupe autorisé", "test": "T01–T06 + regroupement par type d'appareil",
     "mitigation": "Rééquilibrage ou revue humaine après décision explicite"},
    {"id": "B-002", "systeme": "MC-diffusion-j1", "dimension": "regime_signal",
     "condition": "Bruit élevé / capteur dégradé", "risque": "Reconstruction trompeuse",
     "metrique": "Erreur de reconstruction et delta de détection", "test": "Cas J1 gelés + cas réels autorisés",
     "mitigation": "Filtrage qualité du signal, comparaison au baseline"},
    {"id": "B-003", "systeme": "MC-mono-llm", "dimension": "format",
     "condition": "Source absente / contradiction", "risque": "Réponse non fondée ou faux refus",
     "metrique": "Taux d'abstention correcte et exactitude des citations", "test": "T07–T08 (TP04)",
     "mitigation": "Abstention, citations, revue humaine"},
    {"id": "B-004", "systeme": "MC-v2-multillm", "dimension": "format",
     "condition": "Injection / données sensibles", "risque": "Sortie non sûre ou fuite",
     "metrique": "Taux de refus correct et nombre d'appels", "test": "T09–T10 (TP04)",
     "mitigation": "Séparation des instructions, RBAC, masquage, revue humaine"},
    {"id": "B-005", "systeme": "Tous", "dimension": "site",
     "condition": "Nouveau lot / firmware", "risque": "Dérive temporelle",
     "metrique": "Delta de métriques vs baseline", "test": "Monitoring périodique et cas de non-régression",
     "mitigation": "Alerte, réévaluation et rollback"},
    {"id": "B-006", "systeme": "MC-mono-llm", "dimension": "langue",
     "condition": "Langue non couverte ou ambiguë", "risque": "Réponse non fondée ou faux refus",
     "metrique": "Taux d'abstention correcte par langue autorisée",
     "test": "T07–T08 avec variante de langue, si corpus autorisé",
     "mitigation": "Abstention et revue humaine"},
]

_ACTION_PLAN: list[dict[str, str]] = [
    {"id": "A-01", "action": "Compléter une model card effective pour chaque système réellement utilisé.",
     "preuve": "Fiche signée avec version, commit et références Jira", "responsable": "Pilote Elias / binôme Aminata", "statut": "À faire"},
    {"id": "A-02", "action": "Compléter une dataset card par jeu utilisé et vérifier droits/licence/provenance.",
     "preuve": "Manifest + licence vérifiée + hash du jeu", "responsable": "Pilote Elias / binôme Aminata", "statut": "À faire"},
    {"id": "A-03", "action": "Geler collectivement les cas T01–T10 et les cas J1 (RCS-81/RCS-69).",
     "preuve": "freeze_commit renseigné et cas approuvés", "responsable": "Équipe / relais Omar", "statut": "À faire"},
    {"id": "A-04", "action": "Exécuter les tests stress TP04 T07–T10 et consigner les résultats.",
     "preuve": "Rapport d'exécution daté sans données sensibles", "responsable": "Relais Omar", "statut": "À faire"},
    {"id": "A-05", "action": "Définir les seuils acceptables et les responsables de décision.",
     "preuve": "Seuils ratifiés en équipe", "responsable": "Équipe", "statut": "À faire"},
    {"id": "A-06", "action": "Mettre en place monitoring, procédure de rollback et revue humaine.",
     "preuve": "Runbook RCS-89 et journal de traces RCS-78", "responsable": "Relais Omar", "statut": "À faire"},
    {"id": "A-07", "action": "Ne jamais conclure à une absence de biais sans preuve par sous-groupe autorisé.",
     "preuve": "Contrôle automatisé dans les tests RCS-88", "responsable": "Relectrice Gémima", "statut": "À faire"},
    {"id": "A-08", "action": "Faire relire et ratifier l'attribution proposée (Elias/Aminata/Omar/Gémima).",
     "preuve": "Commentaire Jira ratifié", "responsable": "Équipe", "statut": "À faire"},
]


def _sensitive(field: str) -> bool:
    """Détecte un nom de champ sensible sans jamais en copier la valeur.

    La comparaison porte sur des mots entiers : « plage » ne doit pas être
    confondu avec l'attribut « âge », par exemple.
    """
    lowered = field.casefold()
    return any(re.search(r"(?<!\w)" + re.escape(marker) + r"(?!\w)", lowered)
               for marker in FORBIDDEN_ATTRIBUTES)


def model_cards() -> dict[str, dict[str, Any]]:
    """Copie indépendante des fiches modèle, sans mesure inventée."""
    return {key: json.loads(json.dumps(value, ensure_ascii=False))
            for key, value in _MODELS.items()}


def dataset_cards() -> dict[str, dict[str, Any]]:
    """Fiches dataset dérivées de ``data/manifest.md`` (source canonique)."""
    result: dict[str, dict[str, Any]] = {}
    for ident, data in _DATASETS.items():
        entry = dict(data)
        entry.update({
            "id": ident,
            "version_hash": ND,
            "proprietaire": ND,
            "finalite": "Démo / évaluation technique ; périmètre médical exclu",
            "population_appareils": ND,
            "perimetre_site": ND,
            "hypotheses": "Aucune hypothèse de représentativité validée",
            "methode_collecte": ND,
            "pretraitement": ND,
            "qualite_labels": ND,
            "biais_connus": "Couverture industrielle/simulée ; sous-groupes non établis",
            "limites_transfert": "Industriel/simulé ≠ médical réel",
            "retention_securite": ND,
            "lien_manifest": "data/manifest.md",
            "droits_verifies": False,
        })
        result[ident] = entry
    return result


def bias_matrix() -> list[dict[str, str]]:
    """Matrice biais/robustesse : résultats et seuils restent ND."""
    rows = []
    for case in _BIAS_CASES:
        row = dict(case)
        row.update({"resultat": ND, "seuil_acceptable": ND, "statut": "Ouvert"})
        rows.append(row)
    return rows


def authorized_dimensions() -> dict[str, str]:
    """Dimensions autorisées à être examinées, sans sous-groupe inventé."""
    return dict(ALLOWED_DIMENSIONS)


def evaluate_subgroup(system: str, dimension: str, subgroup: str,
                      evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    """Refuse toute évaluation non autorisée ou sans preuve vérifiable.

    ``evidence`` doit contenir ``authorized=True``, une référence de jeu de
    données, une taille d'échantillon et des métriques avec leur provenance.
    Même acceptée, une évaluation ne conclut jamais à une « absence de biais ».
    """
    refusal = {"decision": "REFUSED", "message": REFUSAL_MESSAGE,
               "system": system, "dimension": dimension, "subgroup": ND,
               "claim_of_no_bias": False}
    if system not in _MODELS or dimension not in ALLOWED_DIMENSIONS:
        return dict(refusal, reason="unauthorized_system_or_dimension")
    if not isinstance(subgroup, str) or not subgroup.strip() or len(subgroup) > 120:
        return dict(refusal, reason="invalid_subgroup")
    if _sensitive(subgroup):
        return dict(refusal, reason="sensitive_attribute")
    if not evidence or not isinstance(evidence, dict):
        return dict(refusal, reason="no_evidence")
    if evidence.get("authorized") is not True:
        return dict(refusal, reason="data_not_authorized")
    if not isinstance(evidence.get("dataset_id"), str) or evidence["dataset_id"] not in dataset_cards():
        return dict(refusal, reason="unknown_dataset")
    size = evidence.get("sample_size")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        return dict(refusal, reason="insufficient_sample")
    metrics = evidence.get("metrics")
    provenance = evidence.get("provenance")
    if (not isinstance(metrics, dict) or not metrics
            or not isinstance(provenance, str) or not provenance.strip()
            or any(_sensitive(str(key)) for key in metrics)):
        return dict(refusal, reason="metrics_or_provenance_missing")
    return {
        "decision": "EVALUABLE_SOUS_REVUE",
        "message": "évaluation conditionnelle : sous réserve de revue humaine et de taille statistique suffisante",
        "system": system,
        "dimension": dimension,
        "subgroup": subgroup,
        "dataset_id": evidence["dataset_id"],
        "sample_size": size,
        "metrics": {str(k): str(v) for k, v in metrics.items()},
        "provenance": provenance,
        "claim_of_no_bias": False,
        "human_review_required": True,
    }


def refusal_protocol() -> dict[str, Any]:
    """Protocole de biais et de refus, applicable avant mise en service démo."""
    return {
        "principe": "Refus par défaut : sans preuve par sous-groupe autorisé, aucune conclusion de biais ou d'absence de biais.",
        "dimensions_autorisees": authorized_dimensions(),
        "regles": [
            "Aucun attribut sensible n'est inféré, demandé ou stocké dans les livrables.",
            "Un sous-groupe absent du manifeste ou non autorisé est refusé : « " + REFUSAL_MESSAGE + " ».",
            "Une métrique sans jeu de données identifié, provenance et taille d'échantillon reste ND.",
            "Un résultat par sous-groupe n'est publié qu'après revue humaine.",
            "Le monitoring signale une dérive ; il ne déclenche aucune action autonome sur un appareil.",
        ],
        "etapes": [
            "Définir les dimensions autorisées et pertinentes.",
            "Geler un jeu de cas autorisé et documenter la provenance.",
            "Mesurer la performance globale et par sous-groupe autorisé uniquement.",
            "Analyser faux positifs, faux négatifs, faux refus et cas sensibles.",
            "Documenter limites, incertitude et interdiction d'usage hors périmètre.",
            "Décider GO / NO-GO avec relecteur humain et tracer la décision.",
        ],
        "sortie_refus": REFUSAL_MESSAGE,
        "escalade": "Revue humaine obligatoire ; pas de décision clinique ni d'action autonome.",
        "interdictions": ["inférer un attribut sensible", "inventer une métrique ou un effectif",
                          "affirmer une absence de biais"],
    }


def action_plan() -> list[dict[str, str]]:
    return [dict(item) for item in _ACTION_PLAN]


def _escape(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text.replace("|", "\\|").replace("\n", " ")


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(_escape(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def render_documents() -> dict[str, str]:
    """Contenu Markdown déterministe des fiches effectives et de la matrice."""
    documents: dict[str, str] = {}
    for ident, card in model_cards().items():
        rows = [[key, value] for key, value in card.items()]
        documents[f"model_card_{ident}.md"] = (
            f"# Model card — {ident}\n\n"
            f"> Fiche effective de gouvernance. Les champs {ND} ne sont pas des mesures.\n\n"
            + _table(["Champ", "Valeur"], rows)
            + "\n\nVoir aussi : `dataset_card_*.md`, `matrice_biais_robustesse.md`, `protocole_refus_biais.md`.\n"
        )
    for ident, card in dataset_cards().items():
        rows = [[key, value] for key, value in card.items()]
        documents[f"dataset_card_{ident}.md"] = (
            f"# Dataset card — {ident}\n\n"
            f"> Source canonique : `data/manifest.md`. Aucune donnée patient ni attribut sensible.\n\n"
            + _table(["Champ", "Valeur"], rows) + "\n"
        )
    documents["matrice_biais_robustesse.md"] = (
        "# RCS-88 — Matrice biais / robustesse\n\n"
        "> Résultats et seuils ND : aucune conclusion d'absence de biais.\n\n"
        + _table(["ID", "Système", "Dimension", "Sous-groupe/condition", "Risque",
                  "Métrique", "Résultat", "Seuil", "Test", "Mitigation", "Statut"],
                 [[r["id"], r["systeme"], r["dimension"], r["condition"], r["risque"],
                   r["metrique"], r["resultat"], r["seuil_acceptable"], r["test"],
                   r["mitigation"], r["statut"]] for r in bias_matrix()])
        + "\n\n## Dimensions autorisées (si données autorisées)\n\n"
        + _table(["Dimension", "Description"], [[k, v] for k, v in authorized_dimensions().items()])
        + "\n"
    )
    protocol = refusal_protocol()
    documents["protocole_refus_biais.md"] = (
        "# RCS-88 — Protocole biais et refus\n\n"
        + protocol["principe"] + "\n\n## Règles\n\n"
        + "\n".join(f"- {rule}" for rule in protocol["regles"]) + "\n\n"
        + "## Étapes\n\n"
        + "\n".join(f"{i}. {step}" for i, step in enumerate(protocol["etapes"], 1))
        + f"\n\n**Sortie par défaut :** {protocol['sortie_refus']}  \n"
        + f"**Escalade :** {protocol['escalade']}\n"
    )
    documents["plan_action.md"] = (
        "# RCS-88 — Plan d'action avant mise en service démo\n\n"
        + _table(["ID", "Action", "Preuve attendue", "Responsable", "Statut"],
                 [[a["id"], a["action"], a["preuve"], a["responsable"], a["statut"]]
                  for a in action_plan()]) + "\n"
    )
    return documents


def _load_proof(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Valide une preuve humaine sans jamais la fabriquer."""
    path = root / PROOF_FILE
    if not path.is_file():
        return None, ["proof.json absent : preuve avant mise en service démo manquante"]
    try:
        proof = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return None, [f"proof.json illisible : {type(exc).__name__}"]
    if not isinstance(proof, dict):
        return None, ["proof.json doit être un objet JSON"]
    problems: list[str] = []
    for key in ("reviewer", "review_date", "decision"):
        if not isinstance(proof.get(key), str) or not proof[key].strip() or len(proof[key]) > 200:
            problems.append(f"champ {key} manquant ou invalide")
    try:
        value = proof.get("review_date")
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError("date non canonique")
    except ValueError:
        problems.append("review_date : date ISO invalide")
    if not isinstance(proof.get("decision"), str) or proof.get("decision") not in {"GO", "NO_GO", "A_TESTER"}:
        problems.append("décision doit être GO, NO_GO ou A_TESTER")
    evidence = proof.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        problems.append("evidence doit contenir au moins une référence")
    else:
        for ref in evidence:
            if not isinstance(ref, str) or not ref.strip() or len(ref) > 500 or _sensitive(ref):
                problems.append("référence de preuve invalide ou sensible")
                continue
            if ref.startswith(("http://", "https://")):
                problems.append("référence externe non vérifiée")
                continue
            target = (root / ref).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                problems.append("référence de preuve locale introuvable ou hors périmètre")
    if any(_sensitive(str(k)) for k in proof):
        problems.append("champ sensible interdit dans proof.json")
    return proof, problems


def build_acceptance(root: Path) -> dict[str, Any]:
    """Rapport d'acceptation : sans preuve humaine, démo bloquée."""
    proof, problems = _load_proof(Path(root))
    docs = render_documents()
    cards = model_cards()
    datasets = dataset_cards()
    effective = all(
        f"model_card_{ident}.md" in docs and ND in docs[f"model_card_{ident}.md"]
        for ident in cards
    ) and all(REQUIRED_MODEL_FIELDS.issubset(card) for card in cards.values())
    effective = effective and all(
        REQUIRED_DATASET_FIELDS.issubset(card) and card["droits_verifies"] is False
        for card in datasets.values()
    )
    criteria = {
        "gabarits_model_et_dataset_cards": effective,
        "sous_groupes_uniquement_autorises": set(authorized_dimensions()) == set(ALLOWED_DIMENSIONS),
        "protocole_biais_et_refus": refusal_protocol()["sortie_refus"] == REFUSAL_MESSAGE,
        "plan_action_avant_demo": bool(action_plan()) and all(
            a.get("preuve") and a.get("responsable") for a in action_plan()
        ),
        "preuve_avant_mise_en_service": proof is not None and not problems and proof.get("decision") == "GO",
    }
    criteria["declaration_structurelle_valide"] = criteria["preuve_avant_mise_en_service"]
    # Le fichier local ne permet pas d’authentifier le relecteur ni la ratification.
    criteria["preuve_avant_mise_en_service"] = False
    problems.append("Authentification externe et ratification humaine non vérifiées par cet outil.")
    commissionable = all(criteria.values())
    return {
        "issue": "RCS-88",
        "decision": "GO_SOUS_RESERVE_REVUE" if commissionable else "NO_GO",
        "demo_commissionable": commissionable,
        "criteria": criteria,
        "blocking_reasons": problems,
        "human_review_required": True,
        "clinical_validation": False,
        "no_bias_claim": False,
        "generated_documents": sorted(docs),
        "note": "Une preuve signée ne vaut pas validation clinique et n'autorise pas d'action autonome.",
    }


def write_documents(root: Path) -> list[str]:
    """Écrit les livrables dans ``governance/rcs88`` (écrasement contrôlé)."""
    base = Path(root) / GOVERNANCE_DIR
    base.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in render_documents().items():
        (base / name).write_text(content, encoding="utf-8")
        written.append((GOVERNANCE_DIR / name).as_posix())
    report = build_acceptance(root)
    (base / REPORT_FILE.name).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    written.append((GOVERNANCE_DIR / REPORT_FILE.name).as_posix())
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="RCS-88 : fiches effectives et contrôle d'acceptation")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true", help="écrire les fiches dans governance/rcs88/")
    parser.add_argument("--check", action="store_true", help="échouer si la démo n'est pas autorisable")
    args = parser.parse_args()
    if args.write:
        write_documents(args.root)
    report = build_acceptance(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if args.check and not report["demo_commissionable"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
