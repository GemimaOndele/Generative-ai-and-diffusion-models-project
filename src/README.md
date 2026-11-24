# 🧩 Code applicatif et orchestrateur

- `src/orchestrator.py` est **un squelette** TP04 ; il n'appelle aucun LLM et lève volontairement `NotImplementedError`.
- Le [CodeCarbon local facultatif](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/3) est proposé dans `src/observability/` (PR #3) ; il ne mesure pas les fournisseurs de modèles distants.
- Le [comparateur TP04/TP05](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/9) vérifie le protocole et les résultats de modèles réels **lorsqu'ils existent**.
- Le [prototype web](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/8) est dans `frontend/monitoring/`, sans API.

**Prochaines étapes techniques** : contrats d'interface, contrôles de confidentialité, modèles A/B/licences, tests reproductibles, quotas/budgets, traces `run_id`/`trace_id` et intégration au backend. Aucun contrôle sur une machine réelle.

[Retour au README principal](../README.md)
