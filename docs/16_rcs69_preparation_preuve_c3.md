# RCS-69 — Cas de test C3 et première baseline reproductible

**Gémima (pilote proposé), Aminata (binôme), Omar (relais), Elias (relecteur).**

**Portée :** uniquement préparation et démonstration synthétique. C3 officiel demande une preuve **GenAI/diffusion en 60 minutes**, non accomplie par le seul détecteur de baseline décrit ci-dessous. La famille d'équipements, la licence du dataset et les cas finaux ne sont pas décidés ; la diffusion n'est pas entraînée.

## Choisir une source avant de figer les cas
| Source candidate | Utilisation potentielle | Limite majeure |
|---|---|---|
| UCI AI4I | maintenance industrielle tabulaire synthétique | pas une machine médicale ; adaptation temporelle/diffusion à justifier |
| MIMII DUE | anomalies de machines industrielles acoustiques | pas de télémétrie biomédicale ; modalité audio différente |
| Données hospitalières autorisées | proche du métier | accès, licence, confidentialité et qualité non acquis |
| Simulation traçable | cas reproductibles de développement | ne prouve pas la transférabilité clinique |

**Décisions manquantes :** modalité, provenance/licence, split indépendant, types et étiquettes de panne, critères d'évaluation, modèle génératif exécutable. Ne jamais importer des données de patients non autorisées.

## Grille des dix cas *proposés* (non gelés)
Voir `planning/rcs69_cases_proposed.csv`. La grille couvre 4 cas normaux, 3 anomalies, 1 limite/qualité, 1 sortie de distribution et 1 cas d'usage interdit. Les champs `input_ref`, `dataset_id` et `label_source` sont volontairement **vides**. Ces lignes ne sont pas des données de capteurs, et aucune mesure de qualité n'est revendiquée.

```bash
python -m tools.rcs69_case_audit --cases planning/rcs69_cases_proposed.csv
```

Le validateur doit signaler les champs manquants et indiquer qu'il **ne peut pas geler** ces cas. Une fois les données autorisées sélectionnées, adapter ces 10 cas aux observations réellement disponibles, puis faire relire avant tout gel scientifique.

## Premier test exécutable : baseline de démonstration
```bash
python -m experiments.rcs69_synthetic_baseline
python -m unittest discover -s tests -p 'test_rcs69_c3.py' -v
```

La baseline MAD utilise **une fixture synthétique explicitement créée dans le code** : 20 observations normales pour l'entraînement, 10 observations d'évaluation incluant 2 anomalies injectées artificiellement. Elle montre comment évaluer TP/FP/FN ; **elle n'est pas la baseline officielle C3 sur données réelles**. Tous les scores du script doivent être légendés `synthetic_fixture_not_medical`.

## Déroulé du vrai C3 (60 minutes de séance)
1. 0–10 min : geler 8–10 cas représentatifs avec licence, étiquettes et attentes.
2. 10–25 min : exécuter un **véritable modèle génératif de diffusion**, seed/version/logs, génération/reconstruction de quelques exemples. Le bruitage seul ne prouve rien.
3. 25–40 min : comparer aux mêmes cas avec baseline de règles/ML appropriée et métriques.
4. 40–55 min : montrer au moins un échec/une limite reproductible avec piste de correction.
5. 55–60 min : versionner `docs/03_preuve_technique.md`, `tests/cases.csv`, `experiments/results.csv`, logs/README.

**Interdits :** annoncer une supériorité diffusion, un usage clinique, de la fiabilité ou de l'énergie sans expérience/mesure. Ne pas confondre la démo de MAD avec la preuve officielle.

## Prochaines actions (dépendances)
- Gémima + Aminata : faire approuver la sélection de données et la grille de cas ;
- Omar : vérifier la baseline, les colonnes et les unités ;
- Elias : confirmer le protocole du modèle de diffusion et les métriques ;
- Groupe : réaliser les expériences et revenir sur un cas d'échec.

PR en revue humaine après CI ; aucun gel automatiquement effectué par ce dépôt.
