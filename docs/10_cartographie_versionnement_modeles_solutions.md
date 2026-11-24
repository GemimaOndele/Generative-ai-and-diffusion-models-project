# Cartographie et versionnement des solutions IA — RoboCare Sentinel

**Statut : spécification initiale, à ratifier par le groupe ; aucun modèle opérationnel attesté.** RCS-87. Référence : observation orale du professeur communiquée le 20/11/2026, en complément de C3, TP04 et TP05.

## Carte des composants et des dépendances (cible, non déployée)

```text
Sources autorisées / datasets (manifest, licence, hash, version)
  ├─ données de capteurs ou de maintenance → qualité → baseline règles/ML → diffusion J1
  └─ notices et rapports techniques autorisés → index RAG versionné → mono-LLM / routeur V2 J2
                                              ↓
                   API et règles (droits, citations, refus, budget)
                                              ↓
              Interface web → alerte à valider → suivi d'intervention
                                              ↓
       trace_id + run_id + modèle/données/prompt/code versionnés
                                              ↓
                  monitoring qualité / coût / temps / CO₂e
```

**Règle métier :** aucune action automatique sur un équipement médical réel ni diagnostic patient. L'étude technique sur données industrielles/simulées ne valide pas un usage hospitalier.

## Registre de version (gabarit)
Fichier `governance/model_registry.csv` : **en-tête uniquement**. Une ligne par combinaison *modèle, version, dataset, code et paramétrage effectivement testée*, pas une ligne fictive.

Champs : `artifact_id`, `artifact_type` (baseline/diffusion/mono-LLM/routing/prompt/corpus/index/pipeline/release), `semantic_version`, `parent_id`, `training_or_provider`, `model_id`, `provider_version`, `code_commit_sha`, `dataset_id`, `dataset_version`, `dataset_hash`, `prompt_or_index_version`, `parameters_or_config_hash`, `seed`, `license_and_rights`, `run_id`, `validation_metrics_ref`, `risks_ref`, `approval`, `promotion_state`, `rollback_target`, `last_review_date`.

## Gestion du cycle de vie
1. **Proposition** : fiche d'intention, sources/permissions, risque, coût/temps prévisionnel, ticket Jira.
2. **Expérimentation** : branche `RCS-XX`, code/seed/versions/hashes, preuves et cas gelés.
3. **Revue** : modèle ou modèle fournisseur correctement identifié, résultats/échecs et biais documentés.
4. **Promotion de version** : PR validée, tests, signature de l'approbation en Jira, manifest lié au commit.
5. **Déploiement de démonstration seulement** : journal d'activation/version et environnement, personne responsable.
6. **Surveillance** : qualité des données, comportement/sous-groupes, p95, coût, erreurs, refus, seuils budgétaires.
7. **Rollback** : conserver version précédente stable, procédure de désactivation, journal incident et décision humaine.

Une nouvelle version de code, poids, prompt, corpus ou tarif peut rendre une comparaison précédente non reproductible : enregistrer ce qui a changé et relancer les cas pertinents.

## Responsabilités
- **Ayoub** : registre technique, release et intégration GitHub (RCS-87, pilote proposé).
- **Elias** : modèle, configuration, métriques et limites (binôme RCS-87).
- **Omar** : vérification schéma/manifest et provenance des données.
- **Aminata** : cohérence avec besoins, refus et documentation.
- **Gémima** : cohérence Jira–Drive–GitHub et décisions à ratifier.

**Références transversales :** RCS-18 (risques), RCS-40 (données), RCS-56 à 59 (diffusion), RCS-61/62/75 (LLM), RCS-88 (model cards), RCS-89 (traces), RCS-90 (coût complet).