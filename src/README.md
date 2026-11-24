# 🧩 Code applicatif et orchestrateur

- `src/orchestrator.py` est l'**orchestrateur TP04** (RCS-75) : mono-A, mono-B, routing et cascade bornée, refus/abstention, traces sans secret. Le squelette `NotImplementedError` du socle est remplacé, sans appel LLM réel tant que la configuration live n'est pas validée.
- `src/model_config.py` valide l'identité exacte des deux modèles (nom, version, fournisseur, licence, droits, région, rétention, budget) ; `src/scoring.py` fournit le score automatique limité à la décision observable ; `src/run_benchmark.py` exécute le smoke test démo ou le mode live après autorisation.
- Le budget par cas est réservé **avant** chaque appel : tarifs connus, prompt borné en octets et `max_tokens` transmis au client. Un tarif `ND` ou un montant prévisionnel supérieur au plafond bloque l'appel, y compris le premier appel A de la cascade. Le coût réel ne fait que régler la réservation après coup ; aucun chiffre n'est estimé. `max_calls_per_case` est également vérifié avant chaque requête : à 1, le fallback B est bloqué après A.
- `src/compare_approaches.py` (RCS-22) structure la comparaison A/B/C/V2 sur les cinq axes Jira, vérifie les hypothèses falsifiables et l'absence de mesure inventée, contrôle la séparation J1/J2 (`validate_milestone_protocols()`), le périmètre V2 ≠ optimisation DDPM (`validate_v2_scope()`) et la séquence d'intégration #30/#36 avec CI vérifiée (`validate_integration()`), puis exporte la preuve d'acceptation (`--acceptance --out governance/rcs22_acceptance.json`).
- `src/diffusion_adapter.py` (RCS-57) exécute un mini-DDPM 1D déterministe en bibliothèque standard : deux variantes contrôlées (`base` / `adapte`, seul le conditionnement temporel change), seeds et hyperparamètres figés, logs par époque, mesures recalculées et preuve d'acceptation (`python -m src.diffusion_adapter --acceptance`). Smoke test synthétique J1, sans seuil gelé ni revendication clinique.
- `config/tp04_models.example.json` est le gabarit de configuration live, **sans clé API**.
- Le [CodeCarbon local facultatif](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/3) est proposé dans `src/observability/` (PR #3) ; il ne mesure pas les fournisseurs de modèles distants.
- Le [comparateur TP04/TP05](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/9) vérifie le protocole et les résultats de modèles réels **lorsqu'ils existent**.
- Le [prototype web](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/31) est dans `frontend/monitoring/`, API locale de démonstration uniquement.

**Prochaines étapes techniques** : contrats d'interface, contrôles de confidentialité, modèles A/B/licences, tests reproductibles, quotas/budgets, traces `run_id`/`trace_id` et intégration au backend. Aucun contrôle sur une machine réelle.

[Retour au README principal](../README.md)
