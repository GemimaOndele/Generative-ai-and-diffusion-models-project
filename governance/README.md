# Registres de gouvernance (proposition, RCS-18 / RCS-87 à RCS-90)

**Les CSV de cette PR sont des modèles vides, pas des observations réalisées. Le registre ADR/risques opérationnel est porté par #35 et le contrat de traces par #29.**

| Fichier | Objet | Fréquence de revue |
|---|---|---|
| `model_registry.csv` | Versions du code, modèles, datasets, prompts, paramètres, approbations/rollback | Chaque release et expérimentation nouvelle |
| `templates/risk_register_template.csv` | Événement, personnes, vraisemblance, impact, mesure, preuve et risque résiduel | Sprint, incident, changement de version |
| `cost_register.csv` | Dépenses/sources, unités, coût estimé/réel, matériel et temps | Cadrage, Sprint et fin de lot |
| `worklog_register.csv` | Effort humain estimé/réel (heures) sans prétendre à une rémunération | Chaque tâche/point Sprint |
| `templates/decision_register_template.csv` | Gabarit historique vide : décision, alternatives, raisons, personnes consultées, approbation et révision | Dès qu'un arbitrage change le projet |
| `monitoring_catalog.csv` | KPI, unité, frontière, mode calcul, statut, seuil et réponse à l'alerte | Cadrage puis revue de suivi |
| `templates/trace_event_draft.schema.json` | Contrat minimal de logs end-to-end avec IDs non sensibles | Toute modification de télémétrie |
| `model_card_template.md` / `dataset_card_template.md` | Finalité, données, limites, biais, tests, versions et suivi | Après chaque version utile |

**Règles** : ne jamais inventer de mesure ; marquer `not_available`, utiliser `null` si non mesuré (pas 0), conserver la provenance, la licence, le lien Jira et le SHA Git. Aucun nom de patient, secret/API key, prompt privé ou rapport hospitalier sans autorisation ne doit apparaître ici.

Un registre de modèles se remplit après choix licite des données et expériences effectivement réalisées ; une *model card* vide n'est pas une preuve de qualité ou d'absence de biais.

Voir : `docs/10_cartographie_versionnement_modeles_solutions.md`, `docs/11_cartographie_risques_biais.md`, `docs/12_couts_complets_temps_infrastructure_humain.md`, `docs/13_observabilite_trace_et_runbook.md`.


Utiliser RCS-90 (#5) pour la saisie exécutable des coûts/temps ; les registres génériques ne doivent pas créer une seconde comptabilité. Le schéma de trace historique n'est pas déployable.


Le registre de décisions opérationnel est `governance/adr_register.csv` (RCS-18, #35) ; le modèle CSV historique ne doit pas être alimenté en parallèle.
