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

## Versionnement, risques, coûts et preuves (RCS-87 à RCS-90)
- Toute version de dataset, modèle J1/J2, prompt, index RAG ou configuration doit être reliée à son commit, son hash, sa licence, son expérimentation, sa model/dataset card et sa décision de promotion/rollback. Registres proposés dans la PR #4 : `governance/model_registry.csv`, `governance/risk_register.csv`, `governance/cost_register.csv`.
- Avant toute nouvelle expérience, distinguer jeu de test **gelé** et brouillon ; préciser version/config/seed, coût prévu en euros, temps prévu et matériel. Après exécution, enregistrer les faits réellement observés, échecs, heures, coûts et frontière environnementale (local/API).
- Chaque PR doit indiquer ses risques et biais étudiés, son impact sur les personnes/utilisateurs, les versions affectées, les tests de non-régression et la qualité des preuves (mesuré / calculé / estimé / non disponible).
- Les cas à données sensibles, citations manquantes, injection indirecte ou seuil de budget dépassé doivent conduire à refus, alerte ou validation humaine selon la politique ; jamais à une action autonome sur un appareil médical.

## Fusion et cycle de vie des branches
1. La branche de ticket est créée depuis un `main` à jour, après définition de la tâche dans Jira.
2. La PR reçoit une revue **par une personne distincte de l'auteur**, les contrôles requis GitHub réussissent et les discussions sont résolues. Sur les décisions transverses, attendre l'accord collectif.
3. Fusionner dans `main` puis vérifier le commit et le statut de Jira. Une PR ouverte ou un workflow vert ne suffit pas à dire qu'un livrable est terminé.
4. **Supprimer normalement la branche temporaire après sa fusion**, uniquement si aucun travail non fusionné n'y reste. La PR et les commits resteront visibles dans GitHub. Conserver les versions stables par tags/releases et registry, **pas** par branches personnelles permanentes.
5. Ouvrir la prochaine branche depuis `main` synchronisée, jamais depuis une ancienne branche fusionnée sans vérifier les dépendances.

## Ordre des PR de préparation (au 20/11/2026)
PR #1 structure d'abord, puis revue/harmonisation des PR #2 (Sprint 0/C3/TP04), #3 (TP05/CodeCarbon) et #4 (versions/biais/risques/coûts). Les PR #2 à #4 sont des brouillons non fusionnés. Avant chacune de ces fusions, rafraîchir la branche depuis `main`, résoudre tout conflit sur README et relancer les tests.
