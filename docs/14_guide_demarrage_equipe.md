# Démarrer en groupe sur Jira + GitHub — RoboCare Sentinel

## Premier geste (pour chacun)

1. Se connecter au [dépôt unique](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project) avec son compte, et consulter sa propre mission [Jira RCS](https://gemimakerenondelepourou.atlassian.net/jira/software/projects/RCS/boards/1/backlog).
2. **Ne pas commencer à travailler directement dans `main`**. Cette branche est protégée et ne doit accueillir que des changements relus et acceptés.
3. Vérifier le socle déjà intégré par PR #1 ; relire les PR ouvertes.
4. Sur le socle intégré, revoir PR #2, #3 et #4 pour intégrer les documents préparatoires.
5. Choisir un ticket d'exécution réalisable, définir données/outils et conditions de fin, puis créer une branche depuis `main` **actualisée**.

## Répartition des prochaines actions (non équivalente à une répartition de charge)

- **Gémima** : RCS-17 (collecte disponibilités et chiffrage du Sprint 0), RCS-69, RCS-90.
- **Aminata** : revue de PR #1, RCS-74 (cas TP04, à geler), RCS-84/88.
- **Omar** : revue de PR #1, RCS-16 (DoR/DoD), RCS-71/82.
- **Elias** : revue de PR #1, RCS-75 (LLM A/B, licence/coût), RCS-70/88.
- **Ayoub** : revue PR #1 et tests, RCS-46/48, RCS-87/89.

## Quelle branche « appartient » à qui ?

**Aucune branche permanente par personne.** Les branches existantes sont : `main`, `docs/RCS-46-structure-projet` (PR #1), `docs/RCS-17-sprint0-c3-tp04-preparation` (PR #2), `docs/RCS-81-tp05-finops-green-ethique` (PR #3), `docs/RCS-87-cartographie-versioning-risques-couts` (PR #4).

Pour une tâche nouvelle, le pilote crée `feature/RCS-XX-sujet` / `experiment/RCS-XX-sujet` / `docs/RCS-XX-sujet` depuis `main`, ajoute son binôme, puis ouvre une PR. **La branche est au ticket, pas au membre.** Après fusion, retargeter les PR filles vers main et vérifier leur diff/CI avant de supprimer la branche si aucun travail en cours n'en dépend ; conserver la version stable par tag/release.

## Ordre de gestion et arbitrages

Vérifier le statut actuel du Sprint 0 dans Jira : pas de dates, d'estimations ni de résultats factices. Avant son lancement, collecter heures disponibles, décision de famille de machines, source et licence de dataset, modèles réels disponibles et budget/ressources.

**Ne pas annoncer C3/TP04/TP05 terminés** : une CI de squelette réussie ne mesure ni la fiabilité clinique, ni la qualité d'un LLM, ni le CO₂e d'API distante.
