# 📊 Résultats et traces des expérimentations

**Aucun benchmark LLM ou diffusion réel n'est publié comme validé au 21/11/2026.** Les fichiers CSV et JSONL de préparation peuvent ne contenir que leurs en-têtes ou des fixtures fictives. `ND` veut dire **non disponible**, pas zéro.

### Conditions pour un résultat exploitable
1. Cas, corpus, dataset et version **gelés** avant l'expérience.
2. Commit SHA, paramètres/seed, identifiants/version des modèles et environnement consignés.
3. Mesures réelles (qualité, échecs, latence, coût si connu), avec frontière de mesure et source.
4. Contrôle des réponses refusées, citations, biais et risques ; décision de revue humaine.
5. Aucun token ou coût API converti abusivement en énergie; CodeCarbon local ≠ serveur distant.

**Livrables attendus après exécution** : `results.csv` pour C3, `results/tp04_*.csv` pour TP04, `results/tp05_mesures.csv` pour TP05 (PR #3). Les comparaisons doivent reposer sur les **mêmes cas et unités**, avec incertitudes et statut de disponibilité.

La baseline fictive [RCS-69 / PR #7](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/7) montre seulement le fonctionnement du calcul de métriques ; pas de validation clinique.

### RCS-55 — baseline règles/ML

- `rcs55_baseline_rules_ml.json` : artefact produit par `python experiments/baseline_rules_ml.py --synthetic --out experiments/results/rcs55_baseline_rules_ml.json`. Mesures **réellement calculées** sur le jeu synthétique généré avec `seed=42` : **smoke test non médical**, pas une performance clinique.
- Le z-score de la baseline règles est calibré sur le train uniquement ; les seuils restent non gelés (`ND` pour le seuil de décision final) et le dataset indépendant est à sélectionner.
- Protocole complet : [RCS-55](../docs/08_rcs55_baseline_regles_ml.md). Notebook reproductible : [baseline_rules_ml.ipynb](../baseline_rules_ml.ipynb). Si l'exécution n'est pas possible, l'artefact doit porter `status: "ND"` et une `reason`, sans métrique inventée.

[README principal](../../README.md)
