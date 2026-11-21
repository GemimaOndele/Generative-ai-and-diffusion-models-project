# Audit complet du dépôt GitHub — RoboCare Sentinel

**Date : 21/11/2026** · **Périmètre : `main` + les neuf PR ouvertes** · Ticket Jira : RCS-46/RCS-48, coordination RCS-17.

## Constat principal

- Branche `main` : seulement **README.md** ancien (ne mentionne ni TP05 ni documentation Drive V5/V3.6/V1.3).
- Protection `main` : **ACTIVE** ; PR obligatoire, revue, CI, discussions résolues, suppression et force push bloqués.
- **9 Pull Requests ouvertes et non fusionnées** lors de l'audit, dont PR #1 sans aucune approbation.
- Fichiers de structure et de développement existent sur les branches, pas dans `main`. **Aucune application connectée à un équipement hospitalier n'est confirmée.**
- Les PR #3 et #4 modifient le README avec des versions différentes ; plusieurs PR #2 et #5–9 sont issues de l'ancien `main` ne contenant qu'un README. Risque de **conflits ou écrasements du README à la fusion**.

## Inventaire des PR et dépendances

| PR | Branche | Fichiers ajoutés/modifiés avant audit | Domaine | Décision de fusion |
|---|---|---:|---|---|
| [#1](../../pull/1) | `docs/RCS-46-structure-projet` | 24 | Socle, CONTRIBUTING, CI, TP04 | **Première**, après revue humaine ; nouveau README + assets dans cette PR |
| [#2](../../pull/2) | `docs/RCS-17-sprint0-c3-tp04-preparation` | 6 | Sprint 0, C3, TP04, cas fictifs | Réviser/actualiser après #1 |
| [#3](../../pull/3) | `docs/RCS-81-tp05-finops-green-ethique` | 8 | TP05, CodeCarbon, CSV fictifs vides | README concurrent à retirer ; revue après #1 |
| [#4](../../pull/4) | `docs/RCS-87-cartographie-versioning-risques-couts` | 19 | Governance/model cards, coûts, traces | README concurrent à retirer ; revue après #1 |
| [#5](../../pull/5) | `feature/RCS-90-suivi-couts-complets` | 7 | Calculateur des coûts, CI | Coordonner registres avec #4 |
| [#6](../../pull/6) | `docs/RCS-17-sprint0-readiness` | 5 | Contrôle de capacité et plan Sprint | Éviter doublons du plan #2 |
| [#7](../../pull/7) | `docs/RCS-69-preparer-cas-diffusion` | 6 | Cas C3 et baseline artificielle | Ne pas annoncer diffusion démontrée |
| [#8](../../pull/8) | `feature/RCS-38-monitoring-quatre-vues` | 8 | Prototype web 4 vues fictif | Interface non validée métier |
| [#9](../../pull/9) | `experiment/RCS-81-evaluation-tp04-tp05` | 6 | Comparateur LLM sur cas gelés | Pas de résultats LLM réels |

Ces chiffres correspondent à un **inventaire daté** : vérifier les PR pour l'état courant.

## Résultats et actions d'audit

| Point contrôlé | Observation | Correction / décision |
|---|---|---|
| README de `main` | TP05 absent, contenu dépassé, peu de visuels | Refonte README dans PR #1 : C3/TP04/TP05, gouvernance, 4 vues, équipes, état daté |
| Identité visuelle | Pas de visuels du projet dans `main` | Bannière SVG **animée** de style 3D et schéma d'architecture originaux, en assets locaux |
| Animation README | GitHub ne supporte pas de scène interactive Three.js intégrée au Markdown | Utiliser SVG avec animation SMIL, illustration statique disponible si mouvement réduit/non supporté |
| Liens README | Plusieurs chemins renvoient à des fichiers uniquement en branches | Les PR ouvertes sont explicitement liées ; les liens internes de PR #1 deviennent fonctionnels **après fusion** |
| README dans plusieurs PR | Modifications concurrentes #3 et #4 | Retirer les changements README de #3/#4 (sans enlever leurs autres fichiers) |
| Planification du Sprint | Sprint 0 toujours futur, capacités individuelles non confirmées | Calendrier 23/11–06/12 **proposé**, pas de lancement automatisé ; consultation WhatsApp |
| Code, tests, métriques | Tests CI préparatoires réussis, mais baselines/LLM/diffusion non validées en conditions réelles | Documenter limites et jeux de test ; bloquer toute conclusion clinique |
| Vie privée et données | Aucun dataset médical autorisé confirmé | Maintenir .gitignore, secrets hors Git, charte RGPD et modèles/données sourcés |
| Registres et modèles | Schémas dans PR #4, CodeCarbon local dans PR #3 | Harmoniser versions, unités, ND et coûts, sans doubles facturations |
| Branches | Travail de Gémima réparti sur branches par ticket | Conserver jusqu'aux revues/fusions ; supprimer après merge et vérification |
| Doublons de tâches | RCS-17 dans #2 et #6 ; RCS-81 dans #3 et #9 | #2 = protocole, #6 = contrôle de capacité ; #3 = audit TP05, #9 = évaluateur. Clarifier dans revues |

## Registre des écarts ouverts

1. **Revue PR #1** : demander retours aux quatre membres puis fusion lorsque protection et tests OK.
2. **Consolidation du tronc** : après #1, actualiser branches suivantes à partir de `main`, résoudre les conflits et relancer CI avant fusion.
3. **Cohérence des outils** : deux schémas de suivi de coûts (RCS-90/PR #5 et gouvernance/PR #4) à rapprocher ; idem deux documents Sprint 0.
4. **Données et science** : équipement pilote, licence du dataset et deux LLM réels non validés ; aucun score médical/énergie distant à revendiquer.
5. **Démonstration** : prototype PR #8 à valider métier, puis intégrer à l'architecture choisie ; pas encore de déploiement public confirmé.
6. **Dates & charges** : recueillir accord collectif sur la proposition Sprint 0 avant édition des dates Jira et démarrage effectif.
7. **Cohérence du Drive** : les trois Word collaboratifs ont été reportés dans le Drive selon la coordinatrice ; conserver liens privés en interne.

## Politique de qualité pour les prochaines fusions

- Base PR à jour, CI et sécurité, revue par une personne autre que l'auteur, discussions résolues ;
- Fichier README unique ; éviter toute régression du texte d'accueil après merge ;
- Tests réels distingués des fixtures (les fixtures sont utiles pour l'intégration, pas comme preuve de modèle) ;
- Versionner toute solution et documenter l'incertitude des coûts, délais et émissions ;
- Supprimer une branche temporaire seulement après fusion **et** confirmation d'absence de travail non intégré.

**Ce document décrit un état observé et un plan de corrections, pas une attestation que les neuf PR ont été fusionnées.**
