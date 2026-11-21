# RCS-17 — Plan de lancement du Sprint 0

**Référente Jira : Gémima · binôme Omar · relais Aminata · relecteur Ayoub.**

**Statut au 21/11/2026 : préparation concrète effectuée, mais Sprint Jira toujours FUTUR.** Ne pas inventer de disponibilités/dates/engagements. Les cinq membres doivent confirmer leurs créneaux **en privé** avant de publier des capacités agrégées approuvées.

## Objectif proposé (à approuver)
1. Approuver les règles de contribution et la revue GitHub #1 ;
2. Compléter la charte, la matrice de compétences, l'analyse des dépendances et les accords ;
3. Vérifier la famille de machines pilote et les accès/licences au dataset ;
4. Choisir les modèles et la logique de mesure TP04/TP05 sans dépenser sans accord ;
5. Définir le suivi de risques, coût/temps humain et traces dès l'itération 0.

## Backlog CANDIDAT déjà ajouté au Sprint Jira (non engagé)

| Ticket | Pilote | Livrable/condition |
|---|---|---|
| RCS-11 | Gémima | Charte d'équipe approuvée |
| RCS-13 | Gémima | Matrice compétences autoévaluée (sans niveaux inventés) |
| RCS-14 | Gémima | Trois volets par membre et binômes validés |
| RCS-16 | Omar | DoR/DoD et conventions Jira relues |
| RCS-17 | Gémima | Disponibilités et estimations puis dates validées |
| RCS-46 | Ayoub | Revue PR #1 et socle technique |
| RCS-47 | Ayoub | PR documentaire validée puis fusion |
| RCS-69 | Gémima | Protocole et 8–10 cas diffusion **à geler seulement après dataset** |
| RCS-74 | Aminata | Dix cas TP04 fictifs proposés à revoir, puis gel |
| RCS-75 | Elias | Deux modèles LLM réels A/B justifiés, licences/droits et budget |

Cinq des dix missions candidates sont pilotées par Gémima. **Il ne faut pas prétendre que cette charge est équilibrée** : le groupe doit estimer la durée de chacune et reporter les tâches trop volumineuses.

## Contrôle de disponibilité (aucune information inventée)
- Le fichier `planning/rcs17_capacity.csv` contient cinq lignes avec des champs de capacité **vides** et `approved=pending`.
- `python -m tools.rcs17_sprint0` affiche le nombre de validations, la capacité **partiellement couverte** ou `null`, et des points bloquants.
- L'outil ne contacte pas Jira et **ne démarre pas le Sprint**.
- Ne pas rendre public l'emploi du temps personnel. Les confirmations et créneaux peuvent rester sur le Drive privé ; ne committer qu'un agrégat approuvé ou garder les données localement.

## Définition de Ready (DoR)
Responsable/binôme/relecteur, données et licences autorisées, source et livrable clairs, critères acceptation vérifiables, risques/dépendances identifiés, charge estimée avec capacité.

## Définition de Done (DoD)
Livrable disponible, tests pertinents réussis, preuve/limitations, revue distincte de l'auteur, traçabilité commits/versions/données, mise à jour Jira. Aucun résultat scientifique « effectué » si simulation seulement.

## Ordre de démarrage
1. Relire PR #1 (toujours non fusionnée au dernier contrôle), corriger et faire approuver.
2. Confirmer les capacités/charges, les rôles supplémentaires RCS-81 à RCS-90 et la portée du Sprint.
3. Valider une date de début et de fin ; **seulement ensuite** démarrer le Sprint 0 dans Jira.
4. Intégrer PR #2 (plan et preuves), PR #3 (TP05) et PR #4 (gouvernance) après mise à jour des branches et revues.
5. Ouvrir de nouvelles branches par ticket pour des travaux réellement prêts.

## Réunions à fixer collectivement
Lancement et estimation, synchronisation courte, revue des livrables et rétrospective. Aucune date/heure fixée par cette fiche.

## Dépendances et risques à suivre
- Données de maintenance médicale non acquises ; bascule industrielle/simulée sous mention claire.
- Licence/accès API LLM non décidés ; limites budgétaires avant achat.
- Aucun modèle ni score réel démontré dans les fichiers de cadrage.
- PRs #1–#4 non fusionnées ; prioriser l'approbation de la première.
- Suivi financier RCS-90 et risques RCS-18 dès le début, distincts des tests TP05 finaux.

**Étape humaine restante :** Omar peut vérifier les estimations et la faisabilité ; Ayoub relit le plan ; les cinq membres décident de l'engagement et des dates.

## Proposition de calendrier prêt à soumettre — non validé

Le rythme proposé est un **Sprint 0 court de 2 semaines, lundi 23 novembre → dimanche 6 décembre 2026**, et non un engagement automatique. Le groupe est chargé en autres modules : privilégier les actions **asynchrones** et un petit nombre d'objectifs.

| Date et horaire (Europe/Paris) | Proposition | Engagement |
|---|---|---|
| **Dimanche 22 novembre, 20 h** | Chacun répond « OK », « à ajuster » ou suggère un autre créneau | Consultation WhatsApp, non imposée |
| **Lundi 23 novembre** | Début **seulement si** cinq accords/capacités suffisants et tickets estimés | Sinon glisser d'une semaine |
| **Mardi 24 novembre, 20 h 30–21 h** | Réunion de lancement (visio), ou décision asynchrone si impossible | À confirmer |
| **Jeudi 26 novembre** | Point Jira/WhatsApp asynchrone (PR #1, dataset, blocages) | Pas de réunion obligatoire |
| **Jeudi 3 décembre** | Point Jira/WhatsApp asynchrone (protocoles et budget) | Pas de réunion obligatoire |
| **Dimanche 6 décembre, 18 h–18 h 30** | Revue + décision sur suite du projet | À confirmer |

**Premier objectif minimal raisonnable** : (1) relire/valider la PR #1, (2) valider capacités et règles de travail, (3) fixer famille/données/risques/budget et protocole C3/TP04. Les dix tickets déjà présents dans le Sprint sont un **backlog candidat**, pas dix obligations à livrer en parallèle. Les membres proposent leur capacité réelle ; une suggestion de 2–3 h hebdomadaires par personne est **une hypothèse de planification**, pas une disponibilité connue.

En cas d'absence de consensus avant le 23 novembre, **ne pas démarrer** et proposer le **30 novembre–13 décembre** comme alternative. Aucun changement de dates ni démarrage réel n'est effectué dans Jira par ce document.
