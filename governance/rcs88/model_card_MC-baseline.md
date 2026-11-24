# Model card — MC-baseline

> Fiche effective de gouvernance. Les champs ND ne sont pas des mesures.

| Champ | Valeur |
|---|---|
| nom_systeme | Baseline règles / ML |
| type | Règles / ML |
| version | ND |
| date | ND |
| commit | ND |
| proprietaire | Elias (pilote proposé) / binôme Aminata |
| finalite | Détection d'anomalies et aide à la décision technique, sans décision autonome. |
| hors_perimetre | Diagnostic médical, décision clinique sans revue humaine, action autonome sur appareil biomédical. |
| dataset_ids | ["D-001b", "D-002"] |
| donnees_evaluation | ND |
| hypotheses | ND |
| metriques | {"faux_negatifs": "ND", "faux_positifs": "ND", "p95_latence_ms": "ND", "precision": "ND", "rappel": "ND"} |
| performance_par_sous_groupe | ND |
| limites_connues | Jeu pédagogique non gelé collectivement ; données industrielles/simulées non transférables au médical. |
| limites_transfert | Industriel/simulé ≠ médical réel ; aucune validation clinique. |
| risques | Faux positifs/négatifs, dérive de distribution, biais de couverture. |
| mitigation | Seuils à ratifier, cas gelés T01–T06, revue humaine, journalisation sans données sensibles. |
| conditions_usage | Démo uniquement ; données autorisées et revue humaine des cas sensibles. |
| supervision_humaine | Revue humaine obligatoire pour toute sortie critique ou cas sensible. |
| monitoring | ND (lien RCS-63 / RCS-78 / RCS-86) |
| tests | T01–T06 (TP04) ; RCS-55 / RCS-61 |
| references | RCS-55 (#40), RCS-61 (#34), data/manifest.md |
| statut | Brouillon — à compléter avant démo |

Voir aussi : `dataset_card_*.md`, `matrice_biais_robustesse.md`, `protocole_refus_biais.md`.
