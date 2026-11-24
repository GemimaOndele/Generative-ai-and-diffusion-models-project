# RCS-55 — Baseline règles/ML : protocole, métriques et seuils

> **Statut : protocole formalisé et notebook de rejeu fournis.** `ND` = non disponible, et non égal à zéro. Aucun seuil de détection n'est gelé ; aucune mesure clinique n'est avancée.

## 1. Fiche Jira (reprise fidèle)

- **Tâche** RCS-55, épic **RCS-8**, phase **S3**, priorité **High**, statut **À faire**.
- **Objectif** : « Dataset indépendant, protocole, métriques, seuils et splits. »
- **Critère d'acceptation** : « Notebook baseline reproductible ».
- **Compétence** : Machine Learning.
- **Rôles** : Elias (responsable), Ayoub (binôme), Omar (relais), Gémima (relectrice).
- **Source** : bibliothèque RoboCare Sentinel V3. Aucune date ni estimation n'ayant été décidée, elles ne sont pas complétées ici.

## 2. Dataset et périmètre

- Le jeu cible est un **dataset indépendant** (référence D-002 dans `data/manifest.md`) : origine, droits, unités, traitement des valeurs manquantes et séparation train/val/test doivent être documentés et gelés avant campagne. Il reste `ND` tant qu'il n'est pas sélectionné et validé.
- Aucune donnée sensible ou patient n'est versionnée sans validation explicite des droits, de la confidentialité et du canal de stockage.
- En l'absence de jeu gelé, `--synthetic` génère un jeu artificiel de **smoke test**, étiqueté **non médical** : il valide le calcul et la traçabilité, pas la performance clinique.
- Les deux baselines sont évaluées sur **le même split** et avec les mêmes métriques.

## 3. Protocole

### 3.1 Split reproductible

- Split **train/test stratifié** sur la colonne `label` (`0 = normal`, `1 = anomalie`).
- Paramètres par défaut du module : `seed=42`, `test_size=0.2`. Une autre valeur peut être passée explicitement, mais doit alors être consignée dans l'artefact.
- Même seed + même dataset + même version du code ⇒ même split et mêmes mesures. Le split de validation éventuel reste à définir avec le jeu gelé.

### 3.2 Calibration de la baseline règles — règle anti-fuite

Le z-score est calibré sur le **train uniquement** :

1. `StandardScaler.fit(X_train)` estime la moyenne `mu_train` et l'écart-type `sigma_train` (`scale_`, `ddof=0`) de chaque feature.
2. Ces statistiques sont conservées dans `RuleCalibration` puis appliquées au test : `z_test = (X_test - mu_train) / sigma_train`. Un écart-type nul est remplacé par `1` pour éviter une division par zéro.
3. **Aucune** statistique n'est recalculée sur `X_test` ni sur `train + test` ; les labels du test ne servent qu'à l'évaluation.
4. Décision : anomalie si `max_j |z_test,j| > z_threshold`.

L'artefact consigne `rules_calibration.fitted_on = "train_only"` avec les moyennes et écarts-types utilisés, afin que l'absence de fuite soit vérifiable après coup.

### 3.3 Baselines comparées

- **Règles** : seuil sur le z-score absolu maximal, avec la calibration train définie ci-dessus.
- **IsolationForest** : ajusté sur le train mis à l'échelle, sans labels ; `contamination` est un paramètre de configuration, pas un seuil validé.

### 3.4 Métriques

Calculées sur le **test** uniquement : **precision**, **recall**, **F1** (binaire, `zero_division=0`) et **matrice de confusion** avec les libellés `normal` / `anomaly`. Le rapport de classification est conservé dans l'artefact.

### 3.5 Seuils

| Seuil | Rôle | État |
|---|---|---|
| `z_threshold` | seuil appliqué au z-score calibré sur le train | valeur de configuration du smoke test ; **non gelé** (`ND` comme seuil de détection) |
| `contamination` | paramètre IsolationForest | valeur de configuration du smoke test ; **non gelé** (`ND` comme seuil de détection) |
| Seuil de décision final | seuil opérationnel de détection | **`ND` — à définir avant campagne** |

La calibration des **statistiques** sur le train ne doit pas être confondue avec le gel d'un **seuil numérique** de détection.

## 4. Reproduction

Dépendances : `numpy`, `pandas`, `scikit-learn` (voir `requirements.txt`) ; Jupyter est optionnel pour le notebook.

```bash
# Smoke test synthétique : produit des mesures réelles calculées sur le jeu généré
python experiments/baseline_rules_ml.py --synthetic --out experiments/results/rcs55_baseline_rules_ml.json

# Dataset indépendant (chemin à renseigner après sélection et validation des droits)
python experiments/baseline_rules_ml.py --data <chemin-du-dataset.csv> --out experiments/results/<artefact>.json

# Notebook : ouvrir depuis la racine du dépôt et exécuter toutes les cellules
python -m jupyter notebook experiments/baseline_rules_ml.ipynb

# Rejeu du notebook (cellules exécutées dans l'ordre, sans serveur Jupyter)
python experiments/replay_baseline_notebook.py --out experiments/results/rcs55_notebook_replay.json

# Vérifications locales
python -m unittest discover -s tests -p 'test_*.py'
```

Le rejeu du notebook compare `config`, `dataset`, `protocol`, `thresholds`,
`rules_calibration`, `rules_baseline` et `isolation_forest_baseline` à l'artefact
conservé. La comparaison tolère les écarts de quelques ULP entre plateformes,
mais échoue si une statistique, une métrique ou la calibration `train_only`
change. Aucune preuve de rejeu n'est écrite dans le dépôt par défaut : l'option
`--out` sert à conserver la preuve dans un répertoire de CI ou comme artefact de CI.

## 5. Livrables

| Livrable | Chemin | Contenu / état |
|---|---|---|
| Module reproductible | `experiments/baseline_rules_ml.py` | split stratifié, calibration train-only, deux baselines, artefact JSON |
| Notebook | `experiments/baseline_rules_ml.ipynb` | nbformat 4, fiche Jira, protocole, appels au module, mesures affichées à l'exécution |
| Rejeu du notebook | `experiments/replay_baseline_notebook.py` | exécute les cellules de code et vérifie la concordance avec l'artefact conservé |
| Protocole | `docs/08_rcs55_baseline_regles_ml.md` | dataset, splits, seed, métriques, seuils, commandes, limites |
| Tests | `tests/test_baseline_rules_ml.py` | déterminisme, split stratifié, absence de fuite, bornes des métriques, structure de l'artefact |
| Artefact conservé | `experiments/results/rcs55_baseline_rules_ml.json` | mesures calculées lors du smoke test synthétique ; **non médical** |
| Index des résultats | `experiments/results/README.md` | référence de l'artefact et rappel du statut des preuves |

## 6. Limites et frontière des preuves

- Le jeu synthétique est un **smoke test** : il vérifie le pipeline et la reproductibilité, sans portée clinique. Les classes y sont artificiellement séparables ; aucune mesure, même parfaite, n'est transposable à un jeu clinique.
- **Aucune validation clinique** n'est réalisée ni revendiquée ; le dataset indépendant reste `ND` tant qu'il n'est pas gelé et autorisé.
- **Aucun seuil de détection n'est gelé** : `z_threshold`, `contamination` et le seuil de décision final restent `ND` avant campagne.
- **Résultats réels uniquement** : toute métrique publiée doit provenir d'une exécution traçable sur les données chargées ; le notebook ne fige aucune valeur de métrique. Si l'exécution n'est pas possible, l'artefact porte `status: "ND"` et une `reason`, sans métrique inventée.
- Aucune date, version de modèle, licence, coût, GPU ou résultat clinique n'est affirmé ici. Les tests vérifient le logiciel, pas la pertinence médicale des baselines.

## 7. Référence RCS-55 et doublon à ne pas fusionner tel quel

- La **[PR #40](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/40)** est la référence RCS-55 : elle contient le notebook reproductible, l'artefact réel, la calibration `train_only` et les tests qui vérifient l'absence de fuite et le rejeu du notebook.
- La **[PR #34](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/34)** (RCS-61, baseline mono-LLM) ajoute une ancienne copie de `experiments/baseline_rules_ml.py`. Cette version calcule le z-score avec `X - X.mean()` et `X.std()` sur `X_test` après standardization, donc sur le jeu de test : elle réintroduit une fuite de distribution.
- **Décision** : ne pas fusionner #34 avec ce doublon. Si #34 doit être fusionnée pour RCS-61, supprimer sa copie de `experiments/baseline_rules_ml.py` ou la remplacer par le contenu de la référence #40 avant fusion. Les tests RCS-55 et le rejeu du notebook doivent rester verts.
- Le jeu de données indépendant (D-002) reste à sélectionner, à autoriser et à geler : il est consigné `ND` ici et dans l'artefact. Aucun gel rétroactif n'est appliqué aux exécutions antérieures.

[Index des résultats](../experiments/results/README.md) · [Manifeste des données](../data/manifest.md) · [README principal](../README.md)
