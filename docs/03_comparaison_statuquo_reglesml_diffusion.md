# RCS-22 — Comparaison statu quo, règles/ML et diffusion

> **Statut : analyse cadrée, alignée sur le socle RCS‑75 le 2026‑11‑23.** Ne pas présenter de résultat mesuré non exécuté. Les affirmations doivent rester falsifiables et sourcées. Les modèles exacts, versions, fournisseur et licences restent `ND` jusqu'à validation.

> **Fiche Jira (consultée le 2026‑11‑24)** : source : Backlog RoboCare Sentinel V3 ; phase indicative : S1 (ne pas démarrer le Sprint automatiquement) ; domaine d'origine : BIZ ; catégorie : Fonctionnel ; **compétence à développer : Analyse scientifique**.

## 0. Gouvernance du ticket (RCS-22)

- Responsable Jira : **Elias** (recherche IA, diffusion, RAG, Multi-LLM).
- Binôme de contribution et de progression : **Aminata**.
- Relais en cas de blocage : **Omar**.
- Relectrice des critères d'acceptation : **Gémima**.
- Trois volets : **contribution du pilote** ; **apprentissage accompagné du binôme** ; **recherche/veille documentée** si la mission le requiert (références de veille ci-dessous).
- En cas de blocage : documenter **obstacle, essais et liens** dans le ticket Jira ; solliciter le binôme puis le **relais** ; arbitrer au **point de coordination**. Aucun blocage n'est inventé ici.
- Attribution approuvée collectivement ; Sprint et dates à fixer en planification (non supposés ici), conformément à la phase S1 indicative.

## Compétence à développer : Analyse scientifique

| Volet de la compétence | Preuve dans ce livrable | Statut |
|---|---|---|
| Formuler des hypothèses réfutables | H1–H4 : énoncé, métrique, condition de réfutation | Déclaré, non testé (`ND`) |
| Définir un protocole comparable | Mêmes cas figés, seed/config, cinq axes Jira, mode démo par défaut | `ND` avant RCS-81 |
| Refuser les résultats non étayés | `validate_no_results()` interdit F1/%/ms/€ inventés et tout GO final | Vérifié par tests |
| Documenter les limites et sources | Preuve par approche, source par axe, registre RCS-18 | Traçable |

L'analyse scientifique est donc **méthodologique** ici : elle ne revendique aucune mesure métier tant que le jeu gelé RCS-81 n'existe pas.

## Question

Quelle approche est la plus adaptée, à ce stade du projet RoboCare Sentinel, pour la détection/analyse d'anomalies sur signaux/événements d'équipements, avant toute validation terrain ?

## Approches comparées

| Critère | A. Statu quo (manuel / règles métier existantes) | B. Règles / ML classique | C. Diffusion / GenAI (J1) |
|---|---|---|---|
| Principe | Expertise humaine, procédures, seuils fixes, logs manuels | Règles explicites + modèles supervisés/non supervisés (ex. seuils, IsolationForest, RandomForest selon données) | Modèle génératif apprenant distribution normale pour reconstruire/générer et détecter écarts |
| Données requises | Faibles à moyennes, documentation procédurale | Dataset étiqueté ou partiellement étiqueté, features, historique incidents | Données temporelles suffisantes, prétraitement, compute; souvent plus exigeant |
| Qualité attendue (hypothèse) | Bonne sur cas connus, limitée sur signaux faibles/inédits | Bonne baseline si features pertinentes et labels fiables | Potentielle sur motifs complexes; à prouver sur cas figés |
| Diversité / généralisation | Faible hors procédures connues | Moyenne, dépend des données/features | Potentiellement meilleure sur génération/reconstruction, mais risque d'hallucination/artefacts |
| Coût initial | Faible | Moyen | Moyen à élevé (GPU, expérimentation, tuning) |
| Coût exploitation | Élevé en temps humain | Faible à moyen | Moyen à élevé selon infra/modèle |
| Latence | Variable humaine | Faible | Moyenne à élevée selon modèle |
| Explicabilité | Élevée | Moyenne à élevée (règles/arbre) | Plus faible, nécessite analyse prudente |
| Limites | Oubli, charge, variabilité humaine | Biais labels, dérive, faux positifs/négatifs | Surinterprétation, coût, reproductibilité, absence de preuve clinique |
| Faisabilité POC étudiant | Élevée | Élevée | Moyenne (smoke test faisable, preuve robuste plus coûteuse) |
| Preuve requise | Procédures et retours terrain | Notebook reproductible, métriques, split, confusion matrix | Cas figés, seed, config, logs, baseline comparée, limites |

**Extension V2 (RCS‑75 / RCS‑62) — non validée.** Le routage multi‑LLM n'est pas une quatrième approche : c'est une optimisation de B/C qui choisit le modèle selon la nature du cas, avec repli en cascade si un défaut V1 est prouvé. Aucune supériorité n'est revendiquée ici ; le protocole de comparaison est décrit dans `docs/05_tp04_architecture_v2.md` et `docs/05_tp04_benchmark.md`.

## Hypothèses falsifiables

- **H1 (règles/ML)** : Sur un jeu de cas figés et autorisés, une baseline règles/ML atteint un F1 supérieur au statu quo documenté, avec un taux de faux négatifs acceptable défini avant test.
- **H2 (diffusion)** : Sur les mêmes cas figés, un POC diffusion apporte un gain mesurable (ex. rappel sur anomalies subtiles ou qualité de reconstruction) par rapport à la baseline règles/ML, sans dégrader le coût/latence au-delà du seuil approuvé.
- **H3 (prudence)** : Si le gain n'est pas mesuré ou si le coût/risque dépasse le seuil, la baseline règles/ML reste la référence.
- **H4 (routage V2)** : Le routage multi‑LLM réduit le coût par cas réussi sans perte de qualité par rapport à un mono‑LLM. À vérifier par RCS‑79 ; aucune conclusion n'est figée avant exécution traçable.

Chaque hypothèse est réfutable : H1 par un F1 non supérieur, H2 par l'absence de gain mesurable ou un dépassement coût/latence, H3 par une preuve contraire sur cas figés, H4 par une absence de réduction de coût ou une perte de qualité.

## Critères de décision (à renseigner avant benchmark)

| Critère | Seuil / règle | Poids | Mesuré ? | Protocole / source |
|---|---|---:|---|---|
| Rappel anomalies critiques | À définir | ND | ND | `docs/05_tp04_benchmark.md` |
| Précision / faux positifs | À définir | ND | ND | `docs/05_tp04_benchmark.md` |
| Latence p95 | À définir | ND | ND | `docs/05_tp04_benchmark.md` |
| Coût par cas réussi | À définir | ND | ND | `src/orchestrator.py` (ledger), `docs/05_tp04_benchmark.md` |
| Explicabilité / revue humaine | Obligatoire cas sensibles | ND | ND | RCS-18 (R-002), RCS-39 |
| Reproductibilité | Seed/config/logs requis | ND | ND | `.github/workflows/tp04-tests.yml` |
| Traçabilité des décisions | Trace mono/routing/cascade requise | ND | ND | `tests/test_orchestrator.py` |

Tant que RCS‑81 n'a pas figé collectivement les cas et les seuils d'évaluation, ces valeurs restent `ND` : les contrôles logiciels locaux (tests unitaires, smoke démo, CI) valident le **code**, pas une performance métier.

## Choix justifié (provisoire, non validé)

Le choix retenu **pour la phase actuelle** est : **B. règles/ML comme référence**, avec **C. diffusion comme POC cadré** et **V2 routage comme optimisation à mesurer**, pour trois raisons :

1. **Falsifiabilité** : H1/H2/H4 définissent des conditions explicites de rejet ; aucune d'elles n'est encore confirmée (critères `ND`).
2. **Reproductibilité** : B est la seule approche dont la preuve (notebook, split, métriques) est immédiatement comparable sur les mêmes cas ; C et V2 exigent données/GPU ou appels validés.
3. **Risque maîtrisé** : H3 impose le retour à B si le gain n'est pas mesuré ou si coût/latence dépassent le seuil ; les risques R-002/R-004/R-007 du registre RCS-18 restent ouverts.

Ce choix n'est **pas** un GO final : il sera confirmé, infirmé ou remplacé après benchmark sur cas figés RCS‑81. Aucun modèle, version, fournisseur ou licences exacts ne sont supposés.

### Conditions de renversement (décision réversible)

| Résultat sur cas figés | Effet sur le choix provisoire | Condition à figer avant exécution |
|---|---|---|
| H1 confirmée (B > A) et H2 non confirmée | B reste la référence ; C reste recherche cadrée | Seuil F1/faux négatifs et jeu gelé RCS‑81 |
| H2 confirmée avec gain mesurable et coût/latence dans la limite approuvée | C peut devenir piste principale pour le J1 | Seuils coût/latence et périmètre biomédical explicites |
| H4 confirmée (coût réduit sans perte de qualité) | V2 devient optimisation retenue derrière la référence | Mêmes cas, identité A/B validée, traces comparables |
| Aucune hypothèse confirmée ou seuil non atteint | Maintien de B, GO/NO-GO `ND` | Résultat négatif consigné, pas de revendication de performance |

Aucune de ces conditions n'est déclenchée aujourd'hui : elles sont des règles de décision, pas des résultats.

## Protocole minimal pour trancher

| Axe Jira | Mesure à produire | Statut aujourd'hui | Source / propriétaire |
|---|---|---|---|
| Qualité | Rappel, précision, F1, faux négatifs sur cas figés | ND | `docs/05_tp04_benchmark.md`, RCS-79/RCS-81 |
| Diversité | Couverture des cas, comportement sur motifs inédits | ND | RCS-79 |
| Coût | Coût par cas réussi, coût GPU/appels | ND | `src/orchestrator.py` (ledger), RCS-65/85 |
| Limites | Cas d'échec, abstraction, périmètre biomédical non prouvé | ND | RCS-18 (R-007), RCS-88 |
| Faisabilité | Environnement, données autorisées, reproductibilité CI | ND (hors code) | RCS-56/57/70, CI `tp04-tests.yml` |

Règles du protocole : mêmes cas figés pour A/B/C/V2, seed et config consignés, traces conservées, mode démo par défaut, aucun appel live sans identité A/B validée (RCS-75), aucun seuil inventé avant RCS-81.

## Recommandation provisoire (non validée)

- **Court terme / POC** : commencer par **B. règles/ML** comme baseline reproductible et comparable.
- **J1 recherche** : mener un **POC diffusion** cadré (RCS-56/57/70) en parallèle, sur données autorisées/synthétiques clairement étiquetées, sans revendication clinique.
- **V2 LLM** : utiliser l'implémentation RCS‑75 comme socle de démonstration (mode démo), sans appel live ni modification de modèle tant que l'identité exacte n'est pas validée.
- **Décision finale** : GO/NO-GO uniquement après benchmark sur mêmes cas, avec limites, coûts et risques documentés.

## Liens avec les autres tickets

- RCS-18 : risques R-002 (qualité), R-004 (fournisseur), R-007 (diffusion).
- RCS-55 : baseline règles/ML à livrer par son propre ticket ; aucun script n'est revendiqué présent sur cette branche.
- RCS-56/57/70 : recherche/veille diffusion ; les brouillons locaux ne sont pas versionnés ici, seuls les liens de tickets sont opérationnels.
- RCS-61/62/75/79 : mono-LLM, routing, socle V2 et protocole benchmark.
- RCS-18 : registre des décisions/risques ; R-002/R-004/R-007 restent ouverts.

## Limites

- Aucune donnée médicale réelle n'est analysée ici.
- Aucun score de performance n'est revendiqué sans exécution traçable.
- Les résultats sur données synthétiques ou industrielles ne se transfèrent pas automatiquement au biomédical.
- Les contrôles locaux et la suite de tests CI ne doivent pas être présentés comme une évaluation RCS‑81 validée.

## Outil de comparaison et preuve d'acceptation

- `src/compare_approaches.py` : données structurées A/B/C/V2, matrice axe × approche (qualité, diversité, coût, limites, faisabilité), hypothèses H1–H4 avec métrique et réfutation, protocole `ND`, choix provisoire et condition de renversement.
- `validate_no_results()` contrôle la couverture A/B/C, l'unicité des identifiants, les champs obligatoires, la falsifiabilité, le statut `ND` du protocole et l'absence de mesure chiffrée (F1, pourcentage, latence, coût).
- CLI :

```bash
python -m src.compare_approaches
python -m src.compare_approaches --json
python -m src.compare_approaches --acceptance --out governance/rcs22_acceptance.json
```

- `--acceptance` vérifie **treize critères sur pièces** : trois approches comparées, cinq axes Jira, hypothèses réfutables, choix justifié et réversible, aucune mesure inventée, sources traçables, champs du ticket Jira (source, phase S1, domaine BIZ, catégorie, compétence, rôles, trois volets, procédure de blocage), alignement du Markdown livré sur ces champs, compétence « Analyse scientifique » démontrée par la méthode, séparation J1/J2, périmètre V2 ≠ optimisation DDPM, portée méthodologique (pas une validation scientifique) et séquence d'intégration #30/#36 avec CI vérifiée. Le livrable `governance/rcs22_acceptance.json` est versionné et contrôlé par `tests/test_compare_approaches.py`.
- `--doc <chemin>` permet de contrôler une autre copie du document (utile en CI).
- Tests : `tests/test_compare_approaches.py`, inclus dans la suite `python -m unittest discover -s tests -p 'test_*.py'`.


## Clarification de revue du 24/11 — J1/J2, V2 et intégration

### Workloads et métriques séparés (J1 ≠ J2)

| Jalon | Périmètre | Workload (cas figés) | Métriques | Hypothèses | Tickets |
|---|---|---|---|---|---|
| J1 | Détection/reconstruction de signaux (A/B/C) | C3/RCS-69 et RCS-71 : cas figés de détection/reconstruction | Rappel, précision, F1, faux négatifs, qualité de reconstruction | H1, H2, H3 | C3, RCS-69, RCS-71 |
| J2 | Mono-LLM vs routage/cascade (V2) | RCS-74/RCS-81 : cas documentaires, identité A/B validée | Score observable, coût par cas réussi, latence p95, traçabilité | H4 | RCS-74, RCS-79, RCS-81 |

Règle de comparaison : mêmes cas **à l'intérieur de chaque jalon**, jamais une métrique de détection J1 confrontée à un score documentaire J2. Les **workloads distincts** imposent des jeux de métriques distincts. Les hypothèses H1–H4 sont locales à ce document : leur nomenclature et leurs seuils doivent être harmonisés puis **gelés avant chaque campagne**. Les observations historiques #25/#26 restent exploratoires et ne valident aucune hypothèse.

### V2 n'est pas une optimisation directe du DDPM

V2 est un **choix d'orchestration J2** (mono-LLM vs routage/cascade), distinct de l'approche C. Un détecteur **DDPM** relève de J1/C. Le routage multi-LLM n'est donc **pas une optimisation directe** du DDPM : aucun gain de reconstruction n'est revendiqué ici.

### Portée des contrôles et séquence d'intégration

Les contrôles d'acceptation automatisés sont une preuve de **complétude méthodologique**, **non une validation scientifique** ni une validation Jira/métier.

- Socle TP04 synchronisé avec **#30** ; garde-fous budgétaires conservés : preflight, `max_calls_per_case`, ledger.
- Base temporaire de la PR #36 : **#30** (PR #30 d'abord), puis **retargeter #36 vers main** après intégration de #30.
- CI vérifiée sur `c36b94a` : 4 contrôles au vert ([check-runs](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/commits/c36b94a/check-runs)) ; ne pas intégrer avant ce feu vert.
