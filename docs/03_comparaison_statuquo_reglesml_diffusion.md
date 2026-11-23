# RCS-22 — Comparaison statu quo, règles/ML et diffusion

> **Statut : analyse cadrée.** Ne pas présenter de résultat mesuré non exécuté. Les affirmations doivent rester falsifiables et sourcées.

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

## Hypothèses falsifiables

- **H1 (règles/ML)** : Sur un jeu de cas figés et autorisés, une baseline règles/ML atteint un F1 supérieur au statu quo documenté, avec un taux de faux négatifs acceptable défini avant test.
- **H2 (diffusion)** : Sur les mêmes cas figés, un POC diffusion apporte un gain mesurable (ex. rappel sur anomalies subtiles ou qualité de reconstruction) par rapport à la baseline règles/ML, sans dégrader le coût/latence au-delà du seuil approuvé.
- **H3 (prudence)** : Si le gain n'est pas mesuré ou si le coût/risque dépasse le seuil, la baseline règles/ML reste la référence.

## Critères de décision (à renseigner avant benchmark)

| Critère | Seuil / règle | Poids | Mesuré ? |
|---|---|---:|---|
| Rappel anomalies critiques | À définir | ND | ND |
| Précision / faux positifs | À définir | ND | ND |
| Latence p95 | À définir | ND | ND |
| Coût par cas réussi | À définir | ND | ND |
| Explicabilité / revue humaine | Obligatoire cas sensibles | ND | ND |
| Reproductibilité | Seed/config/logs requis | ND | ND |

## Recommandation provisoire (non validée)

- **Court terme / POC** : commencer par **B. règles/ML** comme baseline reproductible et comparable.
- **J1 recherche** : mener un **POC diffusion** cadré (RCS-57/70) en parallèle, sur données autorisées/synthétiques clairement étiquetées, sans revendication clinique.
- **Décision finale** : GO/NO-GO uniquement après benchmark sur mêmes cas, avec limites, coûts et risques documentés.

## Limites

- Aucune donnée médicale réelle n'est analysée ici.
- Aucun score de performance n'est revendiqué sans exécution traçable.
- Les résultats sur données synthétiques ou industrielles ne se transfèrent pas automatiquement au biomédical.
