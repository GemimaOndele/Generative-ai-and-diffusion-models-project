# Model card — MC-diffusion-j1

> Fiche effective de gouvernance. Les champs ND ne sont pas des mesures.

| Champ | Valeur |
|---|---|
| nom_systeme | Diffusion J1 (adaptateur contrôlé) |
| type | Diffusion |
| version | ND |
| date | ND |
| commit | ND |
| proprietaire | Elias (pilote proposé) / binôme Aminata |
| finalite | Reconstruction et génération contrôlée de signaux pour tester la robustesse, hors usage clinique. |
| hors_perimetre | Génération de preuve clinique, interprétation de signaux patients, décision autonome. |
| dataset_ids | ["D-001b", "D-003"] |
| donnees_evaluation | ND |
| hypotheses | ND |
| metriques | {"delta_detection_vs_baseline": "ND", "erreur_reconstruction": "ND", "p95_latence_ms": "ND", "qualite_signal": "ND"} |
| performance_par_sous_groupe | ND |
| limites_connues | Variantes J1 non validées sur données médicales ; cas J1 à geler collectivement. |
| limites_transfert | Signaux synthétiques/industriels ≠ capteurs médicaux réels. |
| risques | Reconstruction trompeuse sous bruit, fuite de domaine, faux sentiment de performance. |
| mitigation | Filtrage qualité du signal, comparaison baseline vs diffusion sur cas identiques, étiquetage « non médical ». |
| conditions_usage | Expérimentation et démo pédagogique sous revue humaine. |
| supervision_humaine | Revue humaine obligatoire avant toute interprétation d'une reconstruction. |
| monitoring | ND (lien RCS-63 / RCS-78 / RCS-86) |
| tests | Cas J1 gelés à définir ; RCS-57 / RCS-69 / RCS-70 |
| references | RCS-57 (#38), RCS-69, docs/11_cartographie_risques_biais.md |
| statut | Brouillon — à compléter avant démo |

Voir aussi : `dataset_card_*.md`, `matrice_biais_robustesse.md`, `protocole_refus_biais.md`.
