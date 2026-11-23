# Registre des décisions (ADR) et des risques — RoboCare Sentinel

> **Statut : gabarit opérationnel, aligné sur le socle RCS‑75 le 2026‑11‑23.** Ne pas inventer de date, de résultat ou de décision non entérinée. Mettre à jour à chaque sprint/revue. Les valeurs exactes de modèles, versions, fournisseur et licence restent `ND` tant qu'elles ne sont pas validées collectivement.

## 0. Gouvernance du registre (RCS-18)

- Responsable Jira / propriétaire des ADR : **Elias** (recherche IA, diffusion, RAG, Multi-LLM).
- Binôme de contribution et de progression : **Aminata**.
- Relais en cas de blocage : **Gémima**.
- Relecteur des critères d'acceptation : **Omar**.
- Décisions et cotations : à transformer en ADR/risques **après décision réelle** ; aucune valeur chiffrée n'est inventée (commentaires Jira RCS-18 du 17/11 et 20/11/2026).
- Références historiques citées dans Jira : `docs/06_sprint0_plan.md` (PR #2), `governance/risk_register.csv` et `docs/11_cartographie_risques_biais.md` (PR #4). Ces fichiers ne sont pas présents dans le socle actuel (`3b70661`) : les rapatrier ou les recréer avant clôture si le groupe en a besoin.

## 1. Registre des décisions (ADR)

| ID | Date | Statut | Décision | Contexte | Options considérées | Justification | Conséquences | Propriétaire | Relecteur | Liens/preuves |
|---|---|---|---|---|---|---|---|---|---|---|
| ADR-001 | ND | Proposé | Adopter un dépôt Git unique avec branches par ticket et PR relues | Pilotage projet RCS | Mono-repo / multi-repo | Traçabilité, revue, lien Jira-Git | Discipline Git requise | Équipe | Équipe | README.md, RCS-46/47/48 |
| ADR-002 | ND | Proposé | Ne pas inventer de résultats/mesures ; marquer ND/estimé/mesuré | Exigences TP/CM | Publier estimations comme mesures | Intégrité scientifique | Certaines sections restent ND jusqu'à exécution | Elias | Aminata/Omar | Tickets TP04/TP05 |
| ADR-003 | 2026-11-23 | Proposé — en attente de validation | Nommer deux modèles A/B distincts avec identité exacte (provider, version, licence, région, rétention) avant tout appel live | Jalon J2 Multi-LLM | A/B/C… | Exigence RCS‑75 : `validate_pair` vérifie identité, droits et budget ; valeurs réelles non encore figées (`ND`) | Bloque l'exécution live ; le mode démo reste disponible | Elias | Aminata/Omar | RCS-75, `docs/05_tp04_architecture_v2.md`, `src/model_config.py`, `config/tp04_models.example.json`, `tests/test_model_config.py` |
| ADR-004 | 2026-11-23 | Proposé (principe) — à confirmer par benchmark | Patron V2 : **routing** multi‑LLM par défaut ; **cascade** uniquement si un défaut V1 est prouvé et documenté | Défaut V1 à prouver | Routing / Cascade / Critique | Le routing évite d'appeler le second modèle quand ce n'est pas utile ; la cascade sert de repli/critique sur cas incertains (`src/orchestrator.py`) | Traces et coûts enregistrés ; nécessite les 30 tests CI | Elias | Ayoub | RCS-75, RCS-62, `docs/05_tp04_architecture_v2.md`, `src/orchestrator.py`, `tests/test_orchestrator.py`, `.github/workflows/tp04-tests.yml` |
| ADR-005 | 2026-11-23 | Accepté (local) | Unifier le socle : un seul `src/`, `tests/`, `data/` ; supprimer `src/src/`, `tests/tests/`, `data/data/` ; orchestrateur canonique | Revue PR #30 (`ModuleNotFoundError: src.scoring`) | Arborescences dupliquées / socle unique | Une seule source de vérité, importable ; la CI vérifie l'absence de doublons | Branches filles basées sur `3b70661` ; zéro push pour les branches locales | Elias | Omar/Gémima | PR #30, `.github/workflows/tp04-tests.yml`, commit `3b70661` |
| ADR-006 | ND | À décider | Choisir l'équipement pilote | Décision ouverte du Sprint 0 | Équipements candidats (à lister) | À statuer avec le métier et le propriétaire du pilote ; aucune sélection validée | Bloque la définition des cas réels | Elias | Aminata/Omar | RCS-18, RCS-1, PR #2 |
| ADR-007 | ND | À décider | Fixer la source et la licence des données | Décision ouverte du Sprint 0 | Données synthétiques / industrielles / biomédicales | Droits, anonymisation et traçabilité à vérifier avant usage | Aucune donnée réelle ne peut être versionnée avant validation | Elias | Omar/Gémima | RCS-18, RCS-1, PR #2 |
| ADR-008 | ND | À décider | Figer 8–10 cas diffusion pour le POC J1 | Décision ouverte du Sprint 0 | Cas synthétiques / autorisés, 8–10 | Nombre indicatif issu de la planification ; cas et seuils à figer collectivement (RCS-81) | Protocole non comparable tant que les cas ne sont pas figés | Elias | Aminata/Gémima | RCS-18, RCS-81, PR #2 |
| ADR-009 | ND | À décider | Approuver le coût autorisé des appels/du GPU | Décision ouverte du Sprint 0 | Plafond budget / pas de plafond | À arbitrer avec FinOps ; le budget cap existe dans le code mais la valeur reste `ND` | Appels payants bloqués sans accord | Elias | Omar | RCS-18, RCS-65/85/90, PR #2 |
| ADR-010 | ND | À décider | Arrêter charge de travail, Sprint et dates | Décision ouverte du Sprint 0 | Planning à définir | Dates et estimations à fixer en planification, non supposées | Les statuts Jira restent « À faire » jusqu'à arbitrage | Elias | Gémima | RCS-18, RCS-1, PR #2 |

### Modèle ADR court (à copier)

```md
## ADR-XXX — Titre
- Date:
- Statut: Proposé | Accepté | Rejeté | Remplacé
- Contexte:
- Décision:
- Options:
- Justification:
- Conséquences:
- Preuves/liens:
```

## 2. Registre des risques

Échelles proposées (à ratifier en équipe) :
- **Probabilité** : 1 Rare, 2 Peu probable, 3 Possible, 4 Probable, 5 Quasi certain.
- **Gravité/Impact** : 1 Mineur, 2 Modéré, 3 Majeur, 4 Critique, 5 Sévère.
- **Exposition** = Probabilité × Gravité.
- **Exposition résiduelle** = exposition après mitigation effective : `ND` tant qu'une preuve de réduction n'est pas apportée. Aucune cotation résiduelle n'est inventée.

### Matrice probabilité × impact (valeurs d'exposition)

| Gravité → / Probabilité ↓ | 1 Mineur | 2 Modéré | 3 Majeur | 4 Critique | 5 Sévère |
|---|---:|---:|---:|---:|---:|
| 1 Rare | 1 | 2 | 3 | 4 | 5 |
| 2 Peu probable | 2 | 4 | 6 | 8 | 10 |
| 3 Possible | 3 | 6 | 9 | 12 | 15 |
| 4 Probable | 4 | 8 | 12 | 16 | 20 |
| 5 Quasi certain | 5 | 10 | 15 | 20 | 25 |

- Exposition ≥ 12 ou impact 5 : escalade au point de coordination (règle à ratifier).
- GO/NO-GO révisé à chaque Sprint, pas seulement en fin de projet.

| ID | Catégorie | Risque (cause → événement) | Impact (personnes / métier / système) | Prob. | Grav. | Expo. initiale | Expo. résiduelle | Déclencheurs | Mitigation | Contingence | Propriétaire | Reviewer | Ticket/Test | Date revue | Statut |
|---|---|---|---|---:|---:|---:|---|---|---|---|---|---|---|---|---|
| R-001 | Données/RGPD | Données sensibles/patients versionnées → fuite/confidentialité | Personnes : confidentialité patient ; Métier : incident légal/éthique ; Système : fuite de données versionnées | 2 | 5 | 10 | ND | Fichier brut ajouté au repo | `.gitignore`, revue PR, manifest, anonymisation validée | Retrait immédiat, rotation secrets, revue | Équipe | Omar | RCS-18 | ND | Ouvert |
| R-002 | IA/Qualité | Réponse LLM plausible mais fausse → mauvaise décision maintenance | Personnes : décision erronée ; Métier : risque opérationnel ; Système : sortie LLM non fiable | 3 | 5 | 15 | ND | Cas stress, source absente/contradictoire | Validation schéma, abstention, revue humaine, tests T07-T10, 30 tests CI | Bloquer sortie, escalade humain | Elias | Aminata | RCS-61/62/79 | 2026-11-23 | Ouvert |
| R-003 | Biais/Robustesse | Dataset non représentatif → biais/faux négatifs | Personnes : iniquité ; Métier : performance trompeuse ; Système : biais modèle/dataset | 3 | 4 | 12 | ND | Nouveau site/appareil | Model/dataset cards, matrice biais, tests stress | Restreindre périmètre, disclaimer | Elias | Aminata | RCS-88 | ND | Ouvert |
| R-004 | Fournisseur/API | Indisponibilité/changement API/modèle → benchmark non reproductible | Personnes : retard J2 ; Métier : benchmark non reproductible ; Système : API/modèle indisponible ou version drift | 3 | 3 | 9 | ND | Timeout, version drift | Versionner modèle via `src/model_config.py` + `config/tp04_models.example.json`, fallback, mode démo, logs | Retour baseline V1 | Elias | Ayoub | RCS-61/62/75 | 2026-11-23 | Ouvert |
| R-005 | Budget/FinOps | Appels payants non maîtrisés → dépassement budget | Personnes : arrêt expérimentation ; Métier : dépassement budget ; Système : appels non plafonnés | 2 | 4 | 8 | ND | Absence plafond | `--confirm-paid-calls`, budget cap dans l'orchestrateur, suivi coût par succès | Stop appels, mode démo | Elias | Omar | RCS-65/85/90 | 2026-11-23 | Ouvert |
| R-006 | Sécurité | Prompt injection via source RAG/document → action non autorisée/fuite | Personnes : fuite/action non autorisée ; Métier : incident ; Système : injection via source RAG | 3 | 4 | 12 | ND | Source non fiable | Filtrage, allowlist outils, tests injection, revue humaine | Désactiver outil, audit traces | Elias | Ayoub | RCS-62 | ND | Ouvert |
| R-007 | Diffusion | Interprétation abusive d'un smoke test synthétique → fausse preuve J1 | Personnes : décision J1 invalide ; Métier : fausse preuve ; Système : surinterprétation du smoke test | 3 | 4 | 12 | ND | Absence dataset réel | Étiqueter synthétique, protocole J1, preuves reproductibles | Retirer revendication, refaire essai | Elias | Gémima | RCS-57/70 | ND | Ouvert |
| R-008 | Organisation/Code | Arborescences dupliquées → imports cassés/PR non mergeable | Personnes : perte de temps revue ; Métier : PR non mergeable ; Système : imports cassés par doublons | 3 | 3 | 9 | ND | Deux copies du même module | CI duplicate-dir check, socle unique, revue PR #30 | Rebase sur `3b70661`, suppression des doublons | Elias | Omar/Gémima | RCS-75, PR #30 | 2026-11-23 | Mitigé |

## 3. Gouvernance de revue

- Revue minimale : à chaque fin de sprint / avant GO-NO-GO.
- Escalade : tout risque exposition ≥ 12 ou impact 5 doit être porté au point de coordination.
- Liens transversaux : RCS-88 (biais), RCS-89 (alertes), RCS-90 (coûts), RCS-63/78/86 (monitoring) si existants.
- Preuve de clôture : lien vers test, PR, résultat, ou décision ADR.
- Références socle (2026-11-23) : `docs/05_tp04_architecture_v2.md`, `docs/05_tp04_benchmark.md`, `.github/workflows/tp04-tests.yml`. Les contrôles logiciels locaux valident le code ; ils ne constituent pas une évaluation RCS‑81 figée collectivement.
- À chaque sprint : réexaminer exposition initiale **et** résiduelle, réviser le GO/NO-GO, et consigner la date de revue réelle (jamais anticipée).
