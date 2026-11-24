# Projet RoboCare Sentinel — monitoring de CodeCarbon / FinOps (RCS-83, RCS-86)

> **Statut : contrat et instrument local préliminaire. Le tableau de bord applicatif n'est pas implémenté. Aucun calcul CO₂e réel de ce projet n'est publié.**

## Pourquoi ici ?
Les quatre vues du monitoring du MVP comprennent un volet dédié à la **plateforme / qualité du modèle / Green AI**. Ce volet peut montrer le coût par tâche réussie, la qualité, la latence p95, les appels/retries et, si réellement observables, l'énergie consommée par une exécution **locale**. Cela sert le TP05 sans remplacer le jalon J1 diffusion ni créer une fonctionnalité médicale de diagnostic.

## Frontières à distinguer visuellement
- `local_codecarbon_estimate` : CPU/GPU/RAM exécutés sur l'infrastructure instrumentée, granularité dépendante du matériel et du mode ; CO₂e = estimation ; CodeCarbon version, région, PUE doivent être consignés, sans exposer de localisation trop précise.
- `api_remote_unavailable` : CodeCarbon local **ne voit pas** les datacenters des API LLM. Indiquer `ND` sur énergie et CO₂e serveurs, pas `0`.
- `provider_reported` : seulement si un fournisseur livre une métrique environnementale sourcée ; mentionner frontière/source/date/incertitude.
- `cost_provider_reported` : prix/tokens ne sont pas énergie, ni preuve de qualité.

## Contrat événement minimal (à valider avant BDD/JMerise)
`run_id`, `case_id` (pseudonyme), `strategy` (mono-A/B/routing/cascade), `model_id`, `model_version`, `duration_s`, `success` (1/0/ND), `p95_window`, `token_in`, `token_out`, `calls`, `retries`, `cost_eur`, `energy_kwh`, `co2e_kg`, `measurement_status`, `boundary`, `source`, `tool_version`, `tariff_url`, `carbon_factor_source`, `reviewed_by`, `timestamp_utc`.

Interdits : identifiants patients, prompts contenant données personnelles, secrets API et rapports non autorisés. Les résultats `ND` restent **null / champ vide**, pas 0.

## Préparer une expérience réelle et contrôlée
1. Dans un environnement local autorisé (python) : `pip install codecarbon`.
2. Exécuter seulement du calcul local autorisé : training, baseline, inference locale. Prévoir un `run_id` non identifiant et exporter les résultats hors du dépôt Git.
3. Import Python : `from src.observability.codecarbon_local import tracked_local_run, read_local_metrics`.
4. Exemple (à exécuter par le groupe, non exécuté dans le dépôt) :
   ```python
   from src.observability.codecarbon_local import tracked_local_run, read_local_metrics

   with tracked_local_run("RCS-83-test-local"):
       # Appeler ici un VRAI calcul Python local autorisé (pas une requête API distante)
       pass
   result = read_local_metrics("RCS-83-test-local")
   print(result)
   ```
5. Relever durée, énergie kWh, CO₂e kg, version, mode et source **sur ce matériel**, avec statut `estimation_codecarbon`. Garder le `emissions.csv` brut sur la machine de test ; partager après contrôle uniquement des agrégats validés.
6. Comparer des alternatives de même qualité sur le **même test TP04** ; préciser les facteurs externes (matériel, localisation, période, p95).

**Attention :** CodeCarbon peut lire certaines puissances matérielles mais estime d'autres composants ; en mode `process`, GPU reste mesuré/estimé au niveau du GPU partagé (pas uniquement le processus). L'énergie publiée par CodeCarbon peut déjà intégrer le PUE : **ne pas multiplier une seconde fois**. La précision réelle dépend du système.

## Dashboard attendu (futur)
KPI : tâches réussies, coût €/succès, p95, taux d'échecs, appels/retries, énergie locale kWh/succès **si disponible**, kg CO₂e/succès **si disponible**. Filtres modèle/version, stratégie, site (si autorisé), période de mesure, source, frontière, statut (mesuré/calculé/estimé/ND). Graphiques explicatifs de couverture : « seules N/M exécutions sont instrumentées localement ».

## Décision d'intégration
Le contrat final sera aligné avec le MCD/MLD JMerise et le référentiel RGPD. L'interface ne doit pas afficher de nombre spectaculaire sans preuve. Ne pas collecter des données de machines médicales réelles à cette fin sans autorisation.

## Sources
- TP05 ECE 20/11/2026, p. 3.
- https://docs.codecarbon.io/latest/
- https://docs.codecarbon.io/latest/reference/output/
- https://docs.codecarbon.io/latest/how-to/configuration/


Intégration : #29 fournit le contrat canonique, #33 la projection ; CodeCarbon estime le calcul local uniquement. Les métriques non finies/négatives sont refusées, l'absence reste ND. #11/#26 contiennent des résultats historiques distincts, non validés scientifiquement. Aucune exécution API distante n'est mesurée par ce module.
