# RCS — Traçabilité OneDrive ↔ Jira ↔ GitHub — audit du 22 novembre 2026

**Statut : proposition de consolidation pour revue collective, non approuvée.** Analyse du ZIP OneDrive `Projet_GenAI.zip`, des tickets Jira RCS et des branches GitHub consultées. Le ZIP contient des documents de référence et aucun code dans son dossier `code/`. Il ne remplace ni le Jira vivant ni les commits versionnés.

## 1. Hiérarchie des sources et politique de mise à jour

| Élément | Source de référence opérationnelle | Précaution |
|---|---|---|
| Consignes de cours | PDF officiels du répertoire `TPs_Projet/`, `Cours_GenAI_Multi_LLM/` | Ne pas confondre exigences pédagogiques et propositions de groupe |
| Cadrage actuel | `RoboCare_Sentinel/06_Cahier_des_charges/RoboCare_Sentinel_Cahier_des_Charges_Complet_V1_0.docx` et bibliothèque V3.6 | Le nom du fichier ne reflète pas toutes les mises à jour internes ; version/date à inscrire dans le registre |
| Organisation et répartition | `02_Equipe/RoboCare_Sentinel_Fiches_Profils_Equipe_V1.docx` (contenu V5.0) + Jira actuel | Les profils individuels et disponibilités ne doivent pas être publiés intégralement sur GitHub |
| Avancement | Tickets Jira `RCS-*` | 90 tickets à la consultation ; 10 epics, 6 doublons « NE PAS UTILISER » ; les états doivent être recoupés avec les preuves |
| Code, tests et résultats | Branches, commits, PR, Actions GitHub | Une branche ou une CI verte n'est pas une approbation ni un merge |
| Données et droits | `04_Sources/RoboCare_Sentinel_Catalogue_Sources_Donnees_V1.csv` + manifestes versionnés par source | Le CSV de 17 entrées est un inventaire candidat, non une autorisation globale de réutilisation |
| Décision du pilote | `07_JFILES/RCS-19_Matrice_de_choix.xlsx` + Jira RCS-19 | Scores préremplis ≠ votes ; les 15 lignes de critères ne contiennent aucun vote dans les colonnes des cinq personnes ; DEC-02 vide |
| Ancien cadrage | `RoboCare_Sentinel_Feuille_de_route_Cahier_des_charges_v1.docx` | Mentionne maintenance de robots hospitaliers ; **supplanté pour le périmètre actuel**, à conserver seulement comme archive |

## 2. Matrice de correspondance — preuves et écarts

| Domaine / exigence | Document OneDrive | Jira | Développement/preuve GitHub | Situation et action |
|---|---|---|---|---|
| Gouvernance équipe | Fiches profils V5.0 ; bibliothèque §3–4 | RCS-11–18 ; RCS-12 terminé | PR #6 RCS-17 | Disponibilités/capacités non validées ; ne pas démarrer Sprint sans accord |
| Choix machines | RCS-19, RCS-19_v2 ; Matrice de choix / Votes / DEC-02 | RCS-19 en revue | PR #15 : cadrage multi-équipements | 3 familles dans la matrice, pompes proposées ; votes/DEC-02 vides ; vote à compléter |
| AS IS/BPMN | CDC §3 ; pièces annoncées par Aminata dans Jira | RCS-20 en revue | Pas de preuve d'intégration sur main identifiée | 7 étapes décrites par Aminata ; validation du processus avec terrain/relecteurs encore requise |
| Personae/humain dans boucle | CDC §2.4 et §3.4 ; XLS mentionné Jira | RCS-21 en revue | PR #8 RCS-38 : décision fictive locale | Vérifier l'alignement des droits/validations avec les personas |
| openFDA / rappels | Catalogue Sxx ; fiche XLS mentionnée sur Jira | RCS-23 en revue | Corpus documentaire RCS-77, DOC03 | Contexte/rapports uniquement, pas télémétrie ni taux de panne ; contrôler les données personnelles et la fraîcheur |
| AccessGUDID | Catalogue sources | RCS-24 en cours | `docs/RCS-24-audit-accessgudid` (Omar) | Sources d'identification/inventaire, ne pas déduire une courbe de panne |
| Sources de substitution | Catalogue V1 CSV/XLSX/V11 | RCS-25, RCS-27 | `docs/RCS-25-audit-ai4i-mimii-due` | AI4I industriel/synthétique : résultat non transposable automatiquement aux machines médicales |
| Contrat/provenance | CDC §6 ; bibliothèque §7 | RCS-40 en cours | `data/RCS-40-dictionnaire-contrat-donnees` | Revue schéma, champs multiequipement, type de source/usage autorisé |
| MCD/MLD | CDC §7 | RCS-41 en cours ; RCS-42 à faire | `docs/RCS-41-mcd-jmerise`, `feature/RCS-42-mld-sql-jmerise` | Vérifier export JMerise, cohérence SQL et clés avant merge |
| Ingestion | CDC §6.2 | RCS-49 en cours | `feature/RCS-49-ingestion-csv-validations` | CSV + quarantaine/idempotence ; API non encore équivalente ; harmoniser avec schéma |
| Stockage POC | CDC §7–8 | RCS-50 à faire | `feature/RCS-50-stockage-poc` | Branche développée, Jira pas à jour ; comparer avec SQLite propre à la démo RCS-38 |
| Monitoring anomalies | CDC §4, §9 ; bibliothèque §6 | RCS-52 à faire | `feature/RCS-52-vue-mesures-anomalies` (Streamlit) | Branche développée, revue métier et contrat commun RCS-38 |
| Monitoring application | CDC §4, §8–9 | RCS-38 en cours | PR #8 (Gémima) | 4 vues web + API fictive ; rapprochement des schémas avec RCS-49/50/52 nécessaire ; version Pages lecture seule |
| J1 diffusion | CDC §10 ; cours C3 | RCS-69, RCS-70, RCS-71 | PR #7 (signal synthétique) ; `experiment/RCS-71-baseline-vs-diffusion-memes-cas` (Omar) | Protocoles différents, résultats documentés non médicaux ; séparer preuves puis confronter hypothèses |
| J2 Multi-LLM | CDC §11 ; TP04 | RCS-74–79, RCS-81 | `experiment/RCS-77-comparer-mono-routing-cascade` ; PR #9 | Cas, modèles, versions, annotations et métriques à harmoniser ; aucune preuve clinique |
| FinOps/Green AI | TP05 ; CDC §11–12 | RCS-82, RCS-83, RCS-90 | `docs/RCS-82-finops-cout-par-tache-reussie` ; PR #5 | Distinguer euros/temps/CO2e mesuré, estimé, ND ; aucune double facturation |
| RGPD/risques | CDC §13 et §14 | RCS-66, RCS-84, RCS-88 | Garde-fous RCS-77 ; PR #15 | Échec de fidélité T07/T08 : revue, abstention et traçabilité avant usage |
| GitHub/main | bibliothèque §3 ; backlog historique | RCS-46–48 | PR #1–9 ; PR #15 | PR #1 a CI verte mais exige 1 revue indépendante selon règles ; éviter merge simultané de branches recouvrant les mêmes modules |
| Rendu professeur | fiche prévalidation V2 ; CDC | RCS-28–31 ; RCS-68 | Documents répartis dans PR #1–4 | Comparer dernières consignes officielles et versions avant publication |

## 3. Écarts documentaires à traiter

1. **Périmètre** : ancien dossier « robots hospitaliers » ≠ bibliothèque V3.6 / CDC « équipements médicaux ». Ne pas effacer l'archive, indiquer clairement son statut historique.
2. **Versions** : nom de la fiche profils V1 alors que contenu V5.0 ; bibliothèque nom V3 alors que contenu V3.6 ; CDC nom V1_0 avec mises à jour internes. Ne pas renommer automatiquement les sources partagées ; tenir un registre version réelle/date/propriétaire.
3. **Backlog** : CSV du ZIP = 52 lignes de tâches + en-tête ; Jira en contient 90 (10 epics et des doublons balisés). Aucune réimportation CSV sans dédoublonnage ni rapprochement des clés.
4. **Données** : le catalogue V1 CSV donne 17 sources candidates. Les deux XLSX V1/V11 doivent être revus sur place avec le CSV : les registres sont des inventaires, non la preuve d'un pipeline validé pour tous types d'appareils.
5. **Vote** : `Votes` contient les colonnes Gémima, Aminata, Omar, Elias, Ayoub sans notes dans la copie ; onglet `Décision DEC-02` non renseigné. Score indicatif : pompes 3,75 ; scanner 2,60 ; IRM 2,60. Aucun résultat collectif.
6. **Multimodalité** : capteurs, logs, textes, rapports, images *possibles* selon licences/droits. Distinguer catalogue exhaustif et sous-ensemble de démonstration ; un test AI4I tabulaire ne prouve pas du multimodal médical.

## 4. Réconciliation technique à engager avant merge

- Choisir une interface et une source de vérité des données : **ne pas effacer** la vue Streamlit d'Omar ni le frontend RCS-38 de Gémima ; rédiger une table commune `equipment / observation / anomaly / evidence / decision / audit`.
- Partager schémas d'API et unités (date vs index non chronologique AI4I, scores, statut, ids, type de donnée, licence, famille d'équipement et valeur ND).
- Proposer ordre d'intégration `RCS-40 → RCS-41/42 → RCS-49 → RCS-50 → RCS-52`, **sous réserve de revues CI et de vérification des recouvrements**, puis adaptateur RCS-38. Unifier les conflits `src/rcs/db.py`, `src/rcs/ingestion.py` en PR d'intégration, pas en écrasant un fichier.
- Garder la séparation J1 synthétique de Gémima / J1 industriel d'Omar / J2 documentaliste ; associer chaque résultat à sa graine, dataset, licence, commit, protocole, unité de test, matériel et statut.
- Adapter le système aux machines sensibles par **documentation de procédures**, validation humaine et politique de refus ; pas de commande à un respirateur, pas de décision clinique.

## 5. Registre de décisions et responsables de revue proposés

| ID | Question | Porteur/relecteurs | État |
|---|---|---|---|
| DEC-02 | Choix famille pilote J1 et séparément familles documentaires J2 | Aminata + les cinq membres | **Vote non réalisé dans le ZIP** |
| ADR-INT-01 | Schéma commun et source de vérité RCS-38/49/50/52 | Gémima, Omar, Ayoub | Proposition |
| ADR-DATA-01 | Licences/source de substitution et sources médicales autorisées | Omar, Aminata, Elias | À vérifier |
| ADR-MODEL-01 | Jeu gelé et protocole J1/J2 distincts | Elias, Omar, Gémima | À arbitrer |
| ADR-GIT-01 | Ordre PR, revue 1 personne indépendante, CI obligatoire | Ayoub + équipe | Protection GitHub active, procédure collective à formaliser |
| ADR-BUDGET-01 | Coût complet, unité fonctionnelle, énergie/CO2e | Gémima, Omar | Préliminaire |

## 6. Vérifications requises pour fermer cette revue

- Obtenir le vrai fichier Excel partagé **à jour** avant de noter les votes/DEC-02.
- Examiner avec les propriétaires les pièces jointes Jira de RCS-20/21/23 et les exports JMerise ; l'existence annoncée ne signifie pas revue effectuée.
- Confirmer que les codes sur les branches Omar passent les tests obligatoires **après** intégration (CI verte sur branche isolée insuffisante).
- Enregistrer les revues PR et décisions dans Jira ; mettre à jour les tickets « À faire » si une preuve validée justifie un changement.
- Ne pas publier de données patient, clés API ou documents scolaires non redistribuables.

**Cette matrice accompagne la note générale de la PR #15. Elle propose des actions, pas une modification approuvée du CDC ni un verdict de merge.**
