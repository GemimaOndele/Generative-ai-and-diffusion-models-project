# RCS-69 — Première diffusion réellement entraînée sur signaux synthétiques

**Gémima (pilote), Aminata (binôme), Omar (relai), Elias (relecteur technique).**

Il s'agit d'un **POC scientifique sur des courbes artificielles**, non d'un modèle médical. Cette expérience ne remplace pas le choix de données autorisées, la revue des dix cas C3 ni la preuve conforme à remettre au professeur.

## Expérience reproductible

Le script `experiments/rcs69_diffusion_numpy.py` entraîne effectivement un petit MLP à prédire le bruit epsilon sur un processus de diffusion gaussien avec **24 pas de diffusion**. L'entraînement normal-only utilise une perte MSE et Adam NumPy ; le code comprend un **échantillonneur reverse DDPM** (et non un simple bruitage).

Les jeux de données sont des sinusoïdes artificielles avec phases et amplitudes aléatoires, perturbées par des anomalies injectées. La séparation est indépendante et déterministe : **320 train normales, 96 validation normales, 64 test normales et 64 anomalies fictives**.

Le détecteur compare une erreur de reconstruction au seuil du **95e percentile de validation normale**, sans choisir ce seuil sur le test. La baseline MAD utilise le même protocole et le même jeu de test. Les résultats TP/FP/TN/FN, précision, rappel et F1 sont rapportés sans affirmer de supériorité hors de ce jeu synthétique.

## Lancer dans Cursor / terminal

```bash
python -m pip install -r requirements-rcs69.txt
python -m experiments.rcs69_diffusion_numpy --seed 42 --updates 250 --json experiments/results/rcs69_synthetic_poc.json
python -m unittest discover -s tests -p 'test_rcs69_diffusion.py' -v
```

Les **résultats sont créés au moment de l'exécution**. Les CI GitHub Actions publient leur JSON synthétique en *artifact* traçable du run. Ne jamais présenter ce fichier comme une preuve sur des machines médicales réelles.

## Critères scientifiques encore à satisfaire

- Déterminer la famille pilote d'équipements et les données légalement accessibles, avec licence, manifeste et hash.
- Faire approuver **8 à 10 cas** C3 avec étiquettes, provenance, attentes et statut gelé ; la grille `planning/rcs69_cases_proposed.csv` reste non gelée.
- Comparer diffusion et baseline sur des données pertinentes et indépendantes, analyser au moins un échec/une limite et les incertitudes.
- Faire relire les paramètres et choix de score par **Elias**, les métriques par **Omar**, la cohérence métier par **Aminata** ; documenter coût/énergie seulement si mesurables.
- Respecter le cadre pédagogique C3 (preuve 60 min). **Aucun dispositif médical ni patient n'est impliqué.**

**Ce qui est acquis :** le code prouve qu'un modèle de débruitage est réellement entraîné, puis utilisé pour échantillonnage et détection sur un jeu synthétique. **Ce qui reste :** choix et validation de source, protocole C3 réel approuvé et conclusions scientifiques.
