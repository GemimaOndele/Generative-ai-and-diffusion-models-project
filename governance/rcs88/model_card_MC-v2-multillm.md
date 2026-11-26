# Model card — MC-v2-multillm

> Fiche effective de gouvernance. Les champs ND ne sont pas des mesures.

| Champ | Valeur |
|---|---|
| nom_systeme | V2 multi-LLM (routage / cascade) |
| type | Orchestration |
| version | ND |
| date | ND |
| commit | ND |
| proprietaire | Elias (pilote proposé) / binôme Aminata |
| finalite | Orchestrer deux modèles A/B avec routage ou cascade sous contrainte de coût, latence et qualité. |
| hors_perimetre | Boucles autonomes, dépassement du budget, décision clinique automatisée. |
| dataset_ids | ["D-001b"] |
| donnees_evaluation | ND |
| hypotheses | ND |
| metriques | {"appels_par_cas": "ND", "cout_par_cas_eur": "ND", "p95_latence_ms": "ND", "qualite_route": "ND", "taux_abstention_correcte": "ND"} |
| performance_par_sous_groupe | ND |
| limites_connues | Comparaison mono/routage/cascade non figée collectivement ; modèles A/B à valider. |
| limites_transfert | Résultats de démo locaux ≠ performance de production ou médicale. |
| risques | Erreur de routage, retries excessifs, injection, coût imprévu, réponse non fondée. |
| mitigation | max_calls_per_case=2, allow_paid_calls=false par défaut, budgets, abstention, revue humaine. |
| conditions_usage | Démo uniquement ; configuration validée et cas autorisés. |
| supervision_humaine | Revue humaine obligatoire ; le monitoring ne déclenche aucune action autonome. |
| monitoring | ND (lien RCS-63 / RCS-78 / RCS-86) |
| tests | T07–T10 (TP04) ; RCS-77 comparaison des stratégies |
| references | RCS-75, RCS-77, RCS-79, RCS-89 |
| statut | Brouillon — à compléter avant démo |

Voir aussi : `dataset_card_*.md`, `matrice_biais_robustesse.md`, `protocole_refus_biais.md`.
