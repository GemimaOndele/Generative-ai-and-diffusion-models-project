# Model card — MC-mono-llm

> Fiche effective de gouvernance. Les champs ND ne sont pas des mesures.

| Champ | Valeur |
|---|---|
| nom_systeme | Mono-LLM / J2 (RAG) |
| type | LLM fournisseur |
| version | ND |
| date | ND |
| commit | ND |
| proprietaire | Elias (pilote proposé) / binôme Aminata |
| finalite | Aide à l'interprétation documentaire avec citations vérifiables et abstention. |
| hors_perimetre | Réponse sans source, décision clinique, action sur appareil, copie de données non autorisées. |
| dataset_ids | ["D-001b"] |
| donnees_evaluation | ND |
| hypotheses | ND |
| metriques | {"cout_par_cas_eur": "ND", "exactitude_citation": "ND", "faux_refus": "ND", "p95_latence_ms": "ND", "taux_abstention_correcte": "ND"} |
| performance_par_sous_groupe | ND |
| limites_connues | Modèle A/B, licence et droits d'usage non vérifiés dans le socle ; corpus RAG à définir. |
| limites_transfert | Documentation technique autorisée ≠ preuve clinique ; localisation et rétention à vérifier. |
| risques | Hallucination, source absente, injection indirecte, fuite de données, coût/latence. |
| mitigation | Abstention, citations exactes, séparation des instructions, T07–T10, revue humaine. |
| conditions_usage | Données et corpus autorisés uniquement ; aucun appel payant sans accord. |
| supervision_humaine | Revue humaine toujours requise pour une réponse exploitée. |
| monitoring | ND (lien RCS-63 / RCS-78 / RCS-86) |
| tests | T07 source absente, T08 contradiction, T09 injection, T10 données sensibles |
| references | RCS-62, RCS-78 (#27), config/tp04_models.example.json |
| statut | Brouillon — à compléter avant démo |

Voir aussi : `dataset_card_*.md`, `matrice_biais_robustesse.md`, `protocole_refus_biais.md`.
