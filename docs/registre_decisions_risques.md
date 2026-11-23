# Registre des décisions (ADR) et des risques — RoboCare Sentinel

> **Statut : gabarit opérationnel.** Ne pas inventer de date, de résultat ou de décision non entérinée. Mettre à jour à chaque sprint/revue.

## 1. Registre des décisions (ADR)

| ID | Date | Statut | Décision | Contexte | Options considérées | Justification | Conséquences | Propriétaire | Relecteur | Liens/preuves |
|---|---|---|---|---|---|---|---|---|---|---|
| ADR-001 | ND | Proposé | Adopter un dépôt Git unique avec branches par ticket et PR relues | Pilotage projet RCS | Mono-repo / multi-repo | Traçabilité, revue, lien Jira-Git | Discipline Git requise | Équipe | Équipe | README.md, RCS-46/47/48 |
| ADR-002 | ND | Proposé | Ne pas inventer de résultats/mesures ; marquer ND/estimé/mesuré | Exigences TP/CM | Publier estimations comme mesures | Intégrité scientifique | Certaines sections restent ND jusqu'à exécution | Elias | Aminata/Omar | Tickets TP04/TP05 |
| ADR-003 | ND | À décider | Choix modèle A/B pour TP04 V2 | Jalon J2 Multi-LLM | A/B/C... | À compléter après vérification droits/licence/coût/région | Bloque exécution live TP04 | Elias | Aminata | RCS-75, `docs/05_tp04_architecture_v2.md` |
| ADR-004 | ND | À décider | Patron V2 (routing vs cascade) | Défaut V1 à prouver | Routing / Cascade / Critique | Cascade proposée sous réserve de défaut V1 identifié | Implémentation/benchmark à réaliser | Elias | Ayoub | RCS-75, RCS-62 |

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

| ID | Catégorie | Risque (cause → événement → impact) | Prob. | Grav. | Expo. | Déclencheurs | Mitigation | Plan de contingence | Propriétaire | Reviewer | Ticket/Test | Date revue | Statut |
|---|---|---|---:|---:|---:|---|---|---|---|---|---|---|---|
| R-001 | Données/RGPD | Données sensibles/patients versionnées → fuite/confidentialité → incident légal/éthique | 2 | 5 | 10 | Fichier brut ajouté au repo | `.gitignore`, revue PR, manifest, anonymisation validée | Retrait immédiat, rotation secrets, revue | Équipe | Omar | RCS-18 | ND | Ouvert |
| R-002 | IA/Qualité | Réponse LLM plausible mais fausse → mauvaise décision maintenance → risque opérationnel | 3 | 5 | 15 | Cas stress, source absente/contradictoire | Validation schéma, abstention, revue humaine, tests T07-T10 | Bloquer sortie, escalade humain | Elias | Aminata | RCS-62/79 | ND | Ouvert |
| R-003 | Biais/Robustesse | Dataset non représentatif (site/appareil/sous-groupe) → biais/faux négatifs → iniquité/performance trompeuse | 3 | 4 | 12 | Nouveau site/appareil | Model/dataset cards, matrice biais, tests stress | Restreindre périmètre, disclaimer | Elias | Aminata | RCS-88 | ND | Ouvert |
| R-004 | Fournisseur/API | Indisponibilité/changement API/modèle → benchmark non reproductible → retard J2 | 3 | 3 | 9 | Timeout, version drift | Versionner modèle, fallback, mode démo, logs | Retour baseline V1 | Elias | Ayoub | RCS-61/62 | ND | Ouvert |
| R-005 | Budget/FinOps | Appels payants non maîtrisés → dépassement budget → arrêt expérimentation | 2 | 4 | 8 | Absence plafond | `--confirm-paid-calls`, budget cap, suivi coût par succès | Stop appels, mode démo | Elias | Omar | RCS-65/85 | ND | Ouvert |
| R-006 | Sécurité | Prompt injection via source RAG/document → action non autorisée/fuite → incident | 3 | 4 | 12 | Source non fiable | Filtrage, allowlist outils, tests injection, revue humaine | Désactiver outil, audit traces | Elias | Ayoub | RCS-62 | ND | Ouvert |
| R-007 | Diffusion | Interprétation abusive d'un smoke test synthétique → fausse preuve J1 → décision invalide | 3 | 4 | 12 | Absence dataset réel | Étiqueter synthétique, protocole J1, preuves reproductibles | Retirer revendication, refaire essai | Elias | Gémima | RCS-57/70 | ND | Ouvert |

## 3. Gouvernance de revue

- Revue minimale : à chaque fin de sprint / avant GO-NO-GO.
- Escalade : tout risque exposition ≥ 12 ou impact 5 doit être porté au point de coordination.
- Lien avec : RCS-88 (biais), RCS-89 (alertes), RCS-90 (coûts), RCS-63/78/86 (monitoring) si existants.
- Preuve de clôture : lien vers test, PR, résultat, ou décision ADR.
