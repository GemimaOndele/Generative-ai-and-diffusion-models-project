# Index du référentiel technique — RoboCare Sentinel

**20 novembre 2026 — Index des chemins proposés.** Ces fichiers ne sont **pas tous dans `main`** : consulter leurs branches et PR. Une préparation de tests n'est pas une exécution ni un résultat mesuré.

| Domaine | Fichier / branche préparatoire | Propriétaire de travail |
|---|---|---|
| Objectif, cours et équipe | [README racine](../README.md), PR #4 | Gémima / équipe |
| Conventions GitHub et Pull Requests | `CONTRIBUTING.md`, PR #1 | Ayoub |
| Cadrage métier | `docs/01_cadrage.md`, PR #1 | Aminata / Gémima |
| Preuve diffusion C3 | `docs/03_preuve_technique.md`, PR #1 | Elias / Omar |
| Plan d'expérience C3 | `docs/08_cm03_experiment_readiness.md`, PR #2 | Gémima / Elias |
| Sprint 0 | `docs/06_sprint0_plan.md`, PR #2 | Gémima |
| Architecture / benchmark Multi-LLM | `docs/05_tp04_architecture_v2.md` et `05_tp04_benchmark.md`, PR #1 | Elias |
| Tests candidats TP04 | `experiments/tp04_cases_draft.jsonl`, PR #2 | Aminata |
| FinOps, Green AI, éthique TP05 | `docs/06_tp05_finops_green_ethique.md`, PR #3 | Omar / Aminata |
| CodeCarbon local / monitoring cible | `docs/09_codecarbon_monitoring.md`, PR #3 | Ayoub |
| Versions et cartographie des modèles | `docs/10_cartographie_versionnement_modeles_solutions.md`, PR #4 | Ayoub / Elias |
| Matrice de risques et biais | `docs/11_cartographie_risques_biais.md`, PR #4 | Elias / Aminata |
| Coût complet et temps humain | `docs/12_couts_complets_temps_infrastructure_humain.md`, PR #4 | Gémima / Omar |
| Observabilité et gestion d'incident | `docs/13_observabilite_trace_et_runbook.md`, PR #4 | Ayoub / Gémima |
| Registres de gouvernance | `governance/README.md`, PR #4 | Pilotage collectif |

## Ordre de passage

1. **PR #1** : obtenir la revue humaine, résoudre les commentaires et fusionner la structure après CI.
2. **PR #2** : adapter à `main` à jour, valider scénarios C3/TP04 puis revue et fusion.
3. **PR #3** : préciser TP05, CodeCarbon et unité fonctionnelle ; revue après harmonisation du README.
4. **PR #4** : cartographie/versionning, registres et monitoring continu ; harmoniser README et tests avant fusion.
5. **Sprint 0** : actuellement futur, doit être estimé et démarré seulement après accord collectif.

Les versions de référence à déposer dans le Drive : fiche d'équipe V5.0, bibliothèque V3.6, cahier des charges V1.3. Ces livrables ne doivent pas être copiés dans le dépôt public sans accord de l'équipe.

## Liens
- Jira : https://gemimakerenondelepourou.atlassian.net/jira/software/projects/RCS/boards/1/backlog
- Dépôt : https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project
- PR : https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pulls
