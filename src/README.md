# 🧩 Code applicatif et orchestrateur

- `src/orchestrator.py` est l'**orchestrateur TP04** (RCS-75) : mono-A, mono-B, routing et cascade bornée, refus/abstention, traces sans secret. Le squelette `NotImplementedError` du socle est remplacé, sans appel LLM réel tant que la configuration live n'est pas validée.
- `src/model_config.py` valide l'identité exacte des deux modèles (nom, version, fournisseur, licence, droits, région, rétention, budget) ; `src/scoring.py` fournit le score automatique limité à la décision observable ; `src/run_benchmark.py` exécute le smoke test démo ou le mode live après autorisation.
- `src/compare_approaches.py` (RCS-22) structure la comparaison A/B/C/V2 sur les cinq axes Jira, vérifie les hypothèses falsifiables et l'absence de mesure inventée, et exporte la preuve d'acceptation (`--acceptance --out governance/rcs22_acceptance.json`).
- `config/tp04_models.example.json` est le gabarit de configuration live, **sans clé API**.
- Le [CodeCarbon local facultatif](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/3) est proposé dans `src/observability/` (PR #3) ; il ne mesure pas les fournisseurs de modèles distants.
- Le [comparateur TP04/TP05](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/9) vérifie le protocole et les résultats de modèles réels **lorsqu'ils existent**.
- Le [prototype web](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/8) est dans `frontend/monitoring/`, sans API.

**Prochaines étapes techniques** : contrats d'interface, contrôles de confidentialité, modèles A/B/licences, tests reproductibles, quotas/budgets, traces `run_id`/`trace_id` et intégration au backend. Aucun contrôle sur une machine réelle.

[Retour au README principal](../README.md)
