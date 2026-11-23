# RCS-22 — Comparaison statu quo, règles/ML et diffusion

> **Statut : analyse cadrée, alignée sur le socle RCS‑75 le 2026‑11‑23.** Ne pas présenter de résultat mesuré non exécuté. Les affirmations doivent rester falsifiables et sourcées. Les modèles exacts, versions, fournisseur et licences restent `ND` jusqu'à validation.

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
| Risques principaux | Oubli, charge, variabilité humaine | Biais labels, dérive, faux positifs/négatifs | Surinterprétation, coût, reproductibilité, absence de preuve clinique |
| Faisabilité POC étudiant | Élevée | Élevée | Moyenne (smoke test faisable, preuve robuste plus coûteuse) |
| Preuve requise | Procédures et retours terrain | Notebook reproductible, métriques, split, confusion matrix | Cas figés, seed, config, logs, baseline comparée, limites |

**Extension V2 (RCS‑75 / RCS‑62) — non validée.** Le routage multi‑LLM n'est pas une quatrième approche : c'est une optimisation de B/C qui choisit le modèle selon la nature du cas, avec repli en cascade si un défaut V1 est prouvé. Aucune supériorité n'est revendiquée ici ; le protocole de comparaison est décrit dans `docs/05_tp04_architecture_v2.md` et `docs/05_tp04_benchmark.md`.

## Hypothèses falsifiables

- **H1 (règles/ML)** : Sur un jeu de cas figés et autorisés, une baseline règles/ML atteint un F1 supérieur au statu quo documenté, avec un taux de faux négatifs acceptable défini avant test.
- **H2 (diffusion)** : Sur les mêmes cas figés, un POC diffusion apporte un gain mesurable (ex. rappel sur anomalies subtiles ou qualité de reconstruction) par rapport à la baseline règles/ML, sans dégrader le coût/latence au-delà du seuil approuvé.
- **H3 (prudence)** : Si le gain n'est pas mesuré ou si le coût/risque dépasse le seuil, la baseline règles/ML reste la référence.
- **H4 (routage V2)** : Le routage multi‑LLM réduit le coût par cas réussi sans perte de qualité par rapport à un mono‑LLM. À vérifier par RCS‑79 ; aucune conclusion n'est figée avant exécution traçable.

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

Tant que RCS‑81 n'a pas figé collectivement les cas et les seuils d'évaluation, ces valeurs restent `ND` : les contrôles logiciels locaux (30 tests, smoke demo, CI) valident le **code**, pas une performance métier.

## Recommandation provisoire (non validée)

- **Court terme / POC** : commencer par **B. règles/ML** comme baseline reproductible et comparable.
- **J1 recherche** : mener un **POC diffusion** cadré (RCS-56/57/70) en parallèle, sur données autorisées/synthétiques clairement étiquetées, sans revendication clinique.
- **V2 LLM** : utiliser l'implémentation RCS‑75 comme socle de démonstration (mode démo), sans appel live ni modifier de modèle tant que l'identité exacte n'est pas validée.
- **Décision finale** : GO/NO-GO uniquement après benchmark sur mêmes cas, avec limites, coûts et risques documentés.

## Liens avec les autres tickets

- RCS-18 : risques R-002 (qualité), R-004 (fournisseur), R-007 (diffusion).
- RCS-55 : baseline règles/ML (`experiments/baseline_rules_ml.py`).
- RCS-57/70 : POC diffusion (`experiments/diffusion_poc.py`, `docs/06_etude_diffusion_ts_physdiff.md`).
- RCS-61/62/75/79 : mono-LLM, routing, socle V2 et protocole benchmark.

## Limites

- Aucune donnée médicale réelle n'est analysée ici.
- Aucun score de performance n'est revendiqué sans exécution traçable.
- Les résultats sur données synthétiques ou industrielles ne se transfèrent pas automatiquement au biomédical.
- Les contrôles locaux d'Omar et les 30 tests CI ne doivent pas être présentés comme une évaluation RCS‑81 validée.
