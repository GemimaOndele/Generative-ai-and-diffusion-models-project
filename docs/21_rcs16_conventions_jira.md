# RCS-16 — Statuts Jira, types d'issues et conventions (proposition à adopter)

Pilote : Omar · binôme : Elias · relais : Gémima · relectrice des critères : Aminata.

> **Statut : proposition en attente de validation de l'équipe — statut du ticket Jira inchangé.** Ce document détaille
> les éléments de méthode à examiner au Sprint 0 avec `docs/06_sprint0_plan.md` (PR #2, RCS-17), dont il reprend la
> Definition of Ready et la Definition of Done, et avec `CONTRIBUTING.md` (PR #1, RCS-48) pour les branches et commits.
> Une fois adoptée en point de coordination, configurer le workflow du projet RCS (Paramètres du projet → Workflows).

## 1. Workflow

```mermaid
stateDiagram-v2
    [*] --> Backlog
    Backlog --> APreciser: tri
    APreciser --> Pret: DoR satisfaite
    Pret --> EnCours: engagé au Sprint (capacité disponible)
    EnCours --> EnRevue: PR / livrable déposé
    EnRevue --> EnCours: changements demandés
    EnRevue --> Termine: DoD satisfaite (relecteur ≠ pilote)
    EnCours --> Bloque: obstacle documenté
    Bloque --> EnCours: obstacle levé
    Termine --> [*]
```

| Statut | Catégorie Jira | Entrée | Sortie |
|---|---|---|---|
| Backlog | À faire | idée ou exigence | tri : garder / fusionner / rejeter |
| À préciser | À faire | ticket retenu | DoR complète |
| Prêt pour Sprint | À faire | DoR OK | engagement au Sprint planning selon la capacité |
| En cours | En cours | pilote assigné | livrable observable |
| Bloqué | En cours | obstacle : cause, essais, liens, personne sollicitée | obstacle levé ou arbitrage |
| En revue | En cours | PR ou document lié | revue par le relecteur nommé |
| Terminé | Terminé | DoD OK | — |

## 2. Types d'issues

| Type | Usage | Exemple |
|---|---|---|
| Epic | grand domaine (RCS-1 Gouvernance … RCS-10 Qualité) | RCS-9 Multi-LLM, routing et Green AI |
| Story | fonctionnalité utilisateur testable | RCS-49 Ingestion CSV/API |
| Tâche | travail documentaire ou technique non utilisateur | RCS-40 Contrat de données |
| Spike | exploration bornée dans le temps, résultat = fiche + décision | RCS-25 Auditer AI4I et MIMII |
| Bug | écart à un critère d'acceptation déjà validé | « 2ᵉ import crée des doublons » |

## 3. Priorités et blockers

| Priorité | Règle |
|---|---|
| Highest | bloque un jalon (J1/J2) ou un autre membre cette semaine |
| High | nécessaire au Sprint en cours |
| Medium | utile au Sprint suivant |
| Low | amélioration, dette mineure |

Blocker = lien Jira « bloque / est bloqué par » + statut **Bloqué** + commentaire (contexte, tentatives, logs nettoyés,
point de reprise) ; appel au binôme, puis au relais, puis arbitrage en point de coordination (pas d'attente silencieuse).

## 4. Definition of Ready (DoR) — alignée sur `docs/06_sprint0_plan.md`

Un ticket passe à « Prêt pour Sprint » seulement si :
- il est référencé `RCS-XX` avec **responsable, binôme, relais, relecteur** et le lien vers le livrable attendu ;
- l'**objectif**, l'**entrée** et la **sortie** sont explicites, ainsi que les **sources et leurs droits/licences** ;
- les **critères d'acceptation sont vérifiables** (2 à 4, mesurables) ;
- les données nécessaires sont **accessibles et autorisées** ; les **dépendances et risques** sont documentés ;
- la taille est **estimée collectivement** et la **capacité** de l'équipe le permet ;
- aucune tâche d'exécution n'est déclarée prête si un choix de données, de modèle ou de budget reste bloquant.

## 5. Definition of Done (DoD) — alignée sur `docs/06_sprint0_plan.md`

Un ticket passe à « Terminé » seulement si :
- une **preuve est réellement produite** (fichier, code exécuté, log, capture), accessible dans GitHub ou un Drive
  autorisé, et **liée dans Jira** (lien PR + SHA) ; **un gabarit ou une tâche créée ne sont pas un résultat** ;
- les critères d'acceptation sont **vérifiés** ; le résultat est positif **ou** l'échec est traçable ;
- **revue** par le relecteur désigné (≠ pilote) et **tests** automatisés pertinents exécutés ;
- **contrôle de confidentialité** (aucune donnée patient, clé, `.env`) et vérification des **licences** ;
- toute décision médicale ou structurante reste une **décision humaine**, enregistrée ;
- **rien n'est inventé** : modèles et versions, seeds, chiffres, dates, durées, énergie/CO₂e — chaque chiffre porte
  son statut (mesuré / calculé / estimé / ND / hypothétique).

## 6. Nomenclature (cohérente avec `CONTRIBUTING.md`)

- Titre de ticket : `[Domaine] Verbe + objet` (ex. `[DATA] Construire dictionnaire et contrat de données`) ;
  préfixes pédagogiques conservés (`TP04/C4 — …`).
- Branche temporaire par ticket : `docs/`, `feature/`, `data/`, `experiment/`, `fix/`, `test/` + `RCS-XX-sujet`.
- Commit : `type(RCS-XX): description` (ex. `docs(RCS-46): organiser le dépôt`, `test(RCS-74): préparer les cas TP04`).
- PR vers `main` : titre `type(RCS-XX): …`, objectif, fichiers, commande de test, résultats réellement obtenus,
  limites et risques ; fusion squash après revue.
- Étiquettes proposées : `J1`, `J2`, `C3`, `TP04`, `TP05`, `veille`, `rgpd`.

## 7. Modèle de ticket

```
[Domaine] Verbe + objet
Contexte / pourquoi :
Entrée (document, jeu de données, décision) :          Sources et droits :
Sortie / livrable observable (chemin GitHub ou Drive) :
Critères d'acceptation (2–4, vérifiables) :
Responsable · binôme · relais · relecteur :
Dépendances / risques :                                Estimation collective :
Preuve attendue au « Terminé » : lien PR + SHA + test/log + limites
```

## 8. Ticket de démonstration (critère d'acceptation)

Ticket témoin proposé : **RCS-49** (ingestion). Parcours à vérifier dans Jira après adoption du workflow :
Backlog → À préciser (DoR remplie selon §4) → Prêt → En cours (branche `feature/RCS-49-ingestion-csv-validations`)
→ En revue (PR + 4 tests `tests/test_rcs49_ingestion.py` verts) → Terminé (commentaire avec lien PR, SHA, preuve).
Les preuves techniques existent sur la branche ; **la configuration du workflow et les transitions de statut dans
Jira restent à faire par l'équipe** après validation de cette convention.
