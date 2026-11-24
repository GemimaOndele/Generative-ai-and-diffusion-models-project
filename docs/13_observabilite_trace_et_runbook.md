# Traçabilité continue, monitoring et gestion des incidents — RoboCare Sentinel

**Statut : spécification de contrat, non une plateforme déjà déployée.** RCS-89, RCS-86, RCS-78, RCS-63 et RCS-83. Le monitoring débute lors des POC et suit les révisions, et ne doit pas apparaître seulement à la fin.

## Chaîne à tracer
`ticket Jira → commit/PR → dataset_version → model_version / prompt_version / index_version → run_id/trace_id → décision/sortie → test → validation par responsable`.

Des ID pseudonymisés liés au run suffisent ; les noms de patients, clés, prompts sensibles et rapports non autorisés **ne doivent pas figurer dans les logs**.

## Modèle événement historique (non exécutable en production)
Ancien modèle préparatoire `governance/templates/trace_event_draft.schema.json` : `trace_id`, `run_id`, `timestamp_utc`, `component`, `code_commit_sha`, `dataset_version`, `model_version`, `strategy`, `case_id`, `duration_s`, `result_status`, `quality_status`, `calls`, `retries`, `cost_eur`, `energy_kwh`, `co2e_kg`, `measurement_status`, `measurement_boundary`, `source_ref` et `reviewer`.

`null` pour les métriques absentes ; jamais 0 à la place de « non disponible ». CodeCarbon local peut estimer CO₂e sur l'exécution locale ; il ne mesure pas les serveurs d'une API LLM distante.

## Indicateurs et seuils à fixer par le groupe
| Volet | Indicateurs candidats | Déclenchement, action et preuve |
|---|---|---|
| Equipements | nombre d'équipements inventoriés, lacunes de données, alertes validées/rejetées | hausse d'anomalies → vérification technicien ; aucune commande autonome |
| Données / modèles J1 | erreurs d'ingestion, manquants, drift de distribution, FP/FN, perf par catégorie autorisée | dérive détectée → blocage/retest, jamais auto-retraining sans revue |
| Documents / LLM J2 | citations, abstentions, injection, qualité, p95, taux d'erreur, retries | absence de source ou injection → refus, revue et incident |
| Plateforme / FinOps / Green | disponibilité API, coût €/succès, budget consommé, durée, énergie locale, CO₂e estimé et ND distant | alerte budget ou échec → limites appels, retry bornés, revue |
| Gouvernance | versions non reliées, risques élevés ouverts, décisions en attente, PR non relues | blocage de promotion tant que la revue n'est pas faite |

**Seuils non fixés** : les valeurs seront justifiées sur données de développement et validées avec les critères du professeur. Fréquence de revue à convenir (chaque Sprint minimum).

## Runbook d'incident
1. Détecter signal et identifier `trace_id`, version, source, indicateur et statut.
2. Mettre en pause la fonctionnalité ou désactiver une route dangereuse ; conserver l'application en lecture seule si approprié.
3. Ouvrir un ticket Jira « incident » sans y coller de données sensibles.
4. Contacter responsable, binôme, relais, relecteur ; décider STOP/GO et prioriser.
5. Vérifier données, dépendances, labels, corpus, prompt, version modèle, coût et seuil.
6. Corriger dans branche `fix/RCS-XX...`, tester sur le jeu gelé, demander revue, déployer uniquement après validation.
7. Clore avec cause, métriques avant/après et procédure de non-récurrence.

**Contrainte** : aucune métrique de monitoring ne valide la sécurité clinique réelle. La qualification de maintenance appartient au technicien habilité.

Le seul contrat d'intégration exécutable est `data/contracts/trace_event_v1.json` (#29), validé par JSON Schema ; #33 projette les traces et #27 audite les agrégats. Le modèle préparatoire ci-dessus n'est pas un schéma concurrent. Ne pas exporter de texte libre, et appliquer les conditions énergie/ND/frontière du contrat canonique.
