# Sprint 0 — Cadrage et préparation C3/TP04 (RCS-17)

> **Statut : archive de cadrage préparatoire du 20/11, non estimée à cette date. Plan opérationnel unique : RCS-17, PR #6 (`docs/15_rcs17_sprint0_demarrage.md`).** Le Sprint `Sprint 0 — Cadrage et préparation des preuves C3/TP04` (Jira, ID 1) est **future**. Les tâches ci-dessous y figurent déjà, mais leur engagement reste soumis à la capacité des cinq membres.

## Objectif du Sprint
Établir une base collaborative exploitable (règles Jira–GitHub, responsabilité et validation, dépôt et cas de tests), afin de pouvoir exécuter ensuite les preuves scientifiques CM03 (60 min) et TP04 (120 min + atelier facultatif 30 min). **Préparer ≠ exécuter** les expérimentations.

## Backlog candidat sélectionné dans Jira

| Ticket | Référent Jira | Sortie vérifiable | Ordre de traitement |
|---|---|---|---|
| RCS-11 | Gémima | Charte du groupe confirmée dans le document partagé | Indispensable |
| RCS-13 | Gémima | Matrice de compétences 0–3 **auto-évaluée** ; valeurs manquantes laissées vides | Conditionnel |
| RCS-14 | Gémima | Répartition collective confirmée, 3 volets par personne | À vérifier sur pièces |
| RCS-16 | Omar | Workflow Jira, Definition of Ready/Done, blocages et modèle de ticket approuvés | Indispensable |
| RCS-17 | Gémima | Capacités et disponibilités recueillies ; durée et objectif validés en groupe | Indispensable |
| RCS-46 | Ayoub | PR de structure GitHub relue ; règles de protection de `main` prouvées | Indispensable |
| RCS-47 | Ayoub | README versionné, PR approuvée et intégration décidée | Conditionnel à la revue |
| RCS-69 | Gémima | Grille de 8–10 cas C3 définie **après choix du dataset/modalité** | Indispensable |
| RCS-74 | Aminata | Grille de 10 cas TP04 proposée, puis gelée avant benchmark | Indispensable |
| RCS-75 | Elias | Modèles A/B distincts documentés et motif V2 défendable | Indispensable |

**Attention à la capacité :** Gémima pilote cinq tickets sur ces dix, les autres membres entre un et deux. Il ne faut pas interpréter ce nombre comme un effort comparable ; l'équipe doit répartir/reporter après estimation. Les créneaux, dates, heures et points ne sont **pas** préremplis.

## À renseigner au démarrage collectif

| Membre | Créneaux disponibles | Capacité retenue (heures ou points) | Indisponibilités | Confirmation |
|---|---|---|---|---|
| Gémima | À confirmer | À estimer | À déclarer | En attente |
| Aminata | À confirmer | À estimer | À déclarer | En attente |
| Omar | À confirmer | À estimer | À déclarer | En attente |
| Elias | À confirmer | À estimer | À déclarer | En attente |
| Ayoub | À confirmer | À estimer | À déclarer | En attente |

## Definition of Ready (DoR)
- Ticket référencé `RCS-XX`, responsable, binôme, relais, relecteur et lien vers livrable identifiés ;
- objectif, entrée, sortie, sources/licences et critères d'acceptation explicites ;
- données accessibles et autorisées, dépendances/risques documentés ;
- taille estimée collectivement et capacité disponible ;
- pas de tâche d'exécution déclarée prête si choix de données/modèles/budget bloquant.

## Definition of Done (DoD)
- livrable accessible dans GitHub ou Drive autorisé et lié dans Jira ;
- critères d'acceptation **vérifiés**, preuve/log ou capture, résultat positif ou échec traçable ;
- contrôle de confidentialité, revue humaine des décisions médicales et licence des données ;
- tests automatisés pertinents **et** revue du relecteur désigné ;
- aucun résultat fictif, aucune durée/énergie/CO₂e présentée comme mesurée sans instrument.

## Cadence à convenir
Réunion de lancement et estimation → point court de synchronisation → revue des preuves/décisions → rétrospective. Dates à choisir par le groupe. Une difficulté doit être inscrite dans Jira, avec appel au binôme puis au relais.

## Portes de décision
1. **Données C3** : valider famille pilote, jeu industriel/simulé ou réel autorisé, métriques, partition test sans fuite ; voir RCS-19, RCS-25, RCS-27 et RCS-69.
2. **Modèles TP04** : deux **LLM** distincts avec IDs/versions/licences/régions et permissions ; voir RCS-75.
3. **Droits/coût** : ne lancer aucun appel API payant sans accord et ne jamais publier de vrais comptes rendus médicaux.
4. **GitHub** : PR #1 intégrée au socle main ; les PR suivantes restent soumises à approbation ; le CI actuel ne prouve pas la qualité du modèle.

## Liens
- Jira : https://gemimakerenondelepourou.atlassian.net/jira/software/projects/RCS/boards/1/backlog
- PR structure GitHub : https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/1
- C3 : `docs/08_cm03_experiment_readiness.md` dans cette PR
- TP04 : `docs/07_tp04_protocole_preparation.md` et `experiments/tp04_cases_draft.jsonl` dans cette PR

## Conditions transversales supplémentaires issues du rappel professeur (20/11/2026)
- **Dès le Sprint 0**, prévoir estimation des dépenses directes (API/cloud/stockage), des heures humaines, des licences et de l'infrastructure ; suivi sur toute la vie du projet (RCS-90). Aucune valorisation horaire factice n'est une facture réelle.
- Ouvrir ou actualiser le registre des risques existant (RCS-18) avec propriétaire, probabilité/impact et actions préventives ; sous-groupes insuffisamment couverts et biais discutés avec RCS-88.
- Préparer la cartographie versionnée de la solution (RCS-87) et le contrat de traces (RCS-89) avant de déclarer un modèle évalué ou une interface de monitoring effective.
- Les quatre missions RCS-87–90 ne sont **pas ajoutées automatiquement à l'engagement du Sprint** : le groupe doit d'abord estimer les heures/capacités et arbitrer les dépendances. Les coûts/risques sont néanmoins des critères d'entrée à surveiller.
- Les références complètes sont dans la PR #4 et dans la bibliothèque V3.6/CDC V1.3 destinés au Drive. Les preuves techniques C3/TP04 restent non réalisées.


Ce document est historique ; capacités, dates et engagements sont gérés par #6. Les cas TP04 sont des candidats RCS-74 sous responsabilité d'Aminata ; le manifeste RCS-81 (#9) reste bloqué sans gel approuvé. Pour les nouveaux chemins, privilégier le préfixe RCS-XX et l'index unique #4.
