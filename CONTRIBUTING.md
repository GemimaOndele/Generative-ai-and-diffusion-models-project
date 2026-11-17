# Collaboration RoboCare Sentinel — RCS-48

## Avant de coder
1. Choisir un ticket [Jira RCS](https://gemimakerenondelepourou.atlassian.net/jira/software/projects/RCS/boards/1/backlog) et lire le rôle, le binôme, le relais et le relecteur.
2. Vérifier les droits et licences des sources ; ne jamais ajouter de données de patients, journaux réels non autorisés, clés, .env ou données sous licence restrictive.
3. Définir l'objectif, les tests, les critères d'acceptation et les limites.

## Branches et commits
- Branche principale : `main`, destinée au code examiné. Ne pas développer directement sur `main` après la mise en place de la protection.
- Une **branche de travail temporaire par ticket**, pas une branche permanente par personne.
- Préfixes : `docs/RCS-XX-sujet`, `feature/RCS-XX-sujet`, `data/RCS-XX-sujet`, `experiment/RCS-XX-sujet`, `fix/RCS-XX-sujet`, `test/RCS-XX-sujet`.
- Exemple : `experiment/RCS-70-diffusion-c3` ou `feature/RCS-76-orchestrateur-tp04`.
- Commits descriptifs : `docs(RCS-46): organiser le dépôt` ; `test(RCS-74): préparer les cas TP04`.

## Pull Request (PR)
- Ouvrir la PR vers `main`, citer `RCS-XX`, l'objectif, les fichiers, la commande de test, les résultats réellement obtenus, les limites et les risques de sécurité.
- Faire relire par le relecteur Jira ; le binôme contribue et le relais reprend si blocage après coordination.
- Avant fusion : résultats reproductibles ou blocage technique traçable, contrôle de confidentialité, tests et revue. Pas de promesse de qualité clinique.
- Fusion **squash** après revue ; supprimer la branche temporaire si plus utile.

## Si un membre est bloqué
Documenter sur le ticket Jira le contexte, les tentatives, les logs nettoyés et le point de reprise ; solliciter le binôme, puis le relais, puis arbitrer en équipe. Éviter d'attendre en silence et de pousser du code non vérifié.

## Trois volets de progression
Chaque membre participe à une mission principale, une mission de montée en compétences et une activité de veille documentée. Le nombre de tickets n'est pas une estimation de charge.
