# RCS-70 — Démonstration technique de diffusion sur signaux synthétiques (contribution préparatoire)

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

## Vérification locale du 21 novembre 2026

Branche `docs/RCS-69-preparer-cas-diffusion`, référence initiale `041e60a`.
Windows, Python 3.12.2 et NumPy 2.2.6 déjà disponible :

- `python -m unittest discover -s tests -v` : 10 tests réussis.
- `python -m tools.rcs69_case_audit --cases planning/rcs69_cases_proposed.csv` :
  10 cas proposés, 0 gelé ; aucune approbation automatique.
- `python -m experiments.rcs69_synthetic_baseline` : baseline artificielle exécutée.
- `python -m experiments.rcs69_diffusion_numpy --seed 42 --updates 250 --json <fichier-local>` :
  entraînement et échantillonnage exécutés sur les signaux artificiels existants.

Pour cette exécution uniquement, hash du jeu généré :
`ec61f4e1ddcbe6b6e68218152353cb3cf18eb6c2ae490bedcde28b17b78b4947`.
MSE début/fin : 1,033641 / 0,184611 ; F1 MAD : 0,5743 ; F1 débruiteur : 0,9771.
Ce sont des résultats **synthétiques sur cette seed**, pas une preuve de
supériorité générale ou clinique. Le JSON est conservé localement ; aucune
mesure d'énergie, facture ni donnée médicale n'a été inventée ou ajoutée.
La validation des sources et le gel collectif des cas restent à réaliser.


Périmètre de revue : preuve technique synthétique contribuant à RCS-70 (Elias pilote du ticket), pas satisfaction de RCS-69. La grille de RCS-69 reste candidate ; harmoniser avec l'inventaire historique #25 et approuver collectivement un nouveau manifeste avant évaluation. Aucun transfert de responsabilité Jira ni gel rétroactif.
