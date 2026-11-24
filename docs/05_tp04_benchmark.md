# TP04 — Benchmark V2 Multi-LLM et décision · RCS-77 à RCS-79

> **Statut : gabarit du socle complété après rebase sur `main` (`bd1c5d1`).** Aucune mesure de qualité LLM n'est inventée. Les valeurs restent `ND`/`NM`/`À mesurer` tant qu'aucune exécution réelle, traçable et autorisée n'a été réalisée. *NM = non mesuré, et non égal à zéro.* Les seules preuves produites sont des tests logiciels en mode démo.

## 1. Contexte

- **Défaut observé de V1** : à documenter à partir des traces V1 (cas, sortie, résultat attendu, écart).
- **Hypothèse H2** : à compléter après gel du jeu de test.
  - *H2 (brouillon)* : « Sur le jeu de test gelé ______, l'architecture V2 ______ améliore ______ d'au moins ______ par rapport à ______, tout en respectant p95 < ______ et coût < ______. »
- **Modèles** : A/B à renseigner uniquement après vérification licence, droits, région, rétention, coût.

## 2. Protocole

- **Jeu pédagogique proposé** : `experiments/tp04_cases.jsonl` (10 cas) : T01–T04 usuels, T05–T06 complexes, T07 source absente, T08 source contradictoire, T09 injection indirecte, T10 information sensible/hors périmètre. Il n'est **pas gelé collectivement** : RCS-81 maintient ses cas en `pending` avec `freeze_commit` vide. `experiments/test_cases.jsonl` reste vide (contrat du socle).
- **Stratégies comparées** : `mono_a`, `mono_b`, `routing_a_b`, `cascade_a_b`, évaluées sur les **mêmes** cas.
- **Mêmes cas, même ordre, mêmes critères** pour toutes les stratégies.
- Mesurer la **qualité métier séparément de la fidélité aux sources** (citations).
- **Mode démo** : valide l'orchestration uniquement ; ne prouve pas la qualité LLM.
- **Mode live** : interdit sans autorisation explicite coûts/données.

Commande démo :

```bash
python -m src.run_benchmark --mode demo --cases experiments/tp04_cases.jsonl --out experiments/results/tp04_demo
```

### Smoke test démo (orchestration uniquement)

- **Exécuté** : oui, localement par Omar (Windows, Python 3.12.10) puis rejoué après rebase (mode `demo`, clients simulés déterministes). 30 tests (socle + TP04) passent ; `src/run_benchmark.py` produit 4 stratégies × 10 cas dans les artefacts.
- **Artefacts générés localement** : `experiments/results/tp04_demo.csv`, `tp04_demo.jsonl`, `tp04_demo_summary.json` (non publiés comme preuve scientifique).
- **Interprétation** : valide le routage/cascade/traçabilité/scoring automatique de la **décision observable**. **Ne constitue pas** une preuve de qualité LLM, de latence réelle, de coût ou de CO₂e. Les résultats live restent `ND` tant que non exécutés avec modèles A/B autorisés.

## 3. Résultats (à compléter après exécution)

| Stratégie | Qualité moyenne | Qualité cas usuels | Qualité cas stress | p50 latence ms | p95 latence ms | Coût €/cas | Taux échec | Taux abstention/revue | Citations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mono-A | ND | ND | ND | ND | ND | ND | ND | ND | ND |
| mono-B | ND | ND | ND | ND | ND | ND | ND | ND | ND |
| routing A/B | ND | ND | ND | ND | ND | ND | ND | ND | ND |
| cascade A→B | ND | ND | ND | ND | ND | ND | ND | ND | ND |

*ND/NM = non mesuré, et non égal à zéro. Distinguer les coûts de routage, de validation, de retries et de supervision humaine si connus.*

## 4. Analyse par catégorie

| Case | Catégorie | mono-A | mono-B | V2 | Commentaire |
|---|---|---|---|---|---|
| T01-T04 | usuels | ND | ND | ND |  |
| T05-T06 | complexes | ND | ND | ND |  |
| T07 | source absente | ND | ND | ND |  |
| T08 | contradiction | ND | ND | ND |  |
| T09 | injection | ND | ND | ND |  |
| T10 | sensible/hors périmètre | ND | ND | ND |  |

## 5. Coûts, latence, énergie

- **Coût** : ne pas déduire d'un prix API seul sans calcul par tokens/appels. Laisser `ND` si inconnu. Distinguer routage, validation, retries et supervision humaine si connus.
- **Énergie/CO₂e** : `mesuré` / `estimé` / `non disponible (NM)`. Ne pas inventer. Le CO₂e n'est pas déductible du coût API seul. Préciser énergie, unité, PUE, intensité carbone, date/source si estimé, et un **périmètre commun** (local/API/hybride) pour toutes les stratégies.
- **Latence** : rapporter p50/p95 si mesuré ; inclure timeouts/retries.

## 6. Ablations / variantes (optionnel)

| Variante | Changement unique | Impact qualité | Impact p95 | Impact coût | Décision |
|---|---|---:|---:|---:|---|
| V2 sans fallback | désactiver B | ND | ND | ND | ND |

## 7. Décision GO / NO-GO

- **Décision** : ND (aucune exécution réelle documentée).
- **Raison** : compléter après benchmark.
- **Décision à prendre après résultats.** Motifs de refus possibles : dégradation sur cas critiques, transfert interdit, coût ou p95 dépassé, réponses dangereuses.
- **Retour V1 requis si** : dégradation cas critiques, dépassement seuils qualité/p95/budget approuvés, ou transfert de données interdit.
- **Prochaine expérience** : exécuter mono-A/mono-B/V2 sur cas gelés avec modèles autorisés, puis compléter ce rapport avec traces.

## 8. Reproductibilité

Versions des modèles et des composants, commandes exécutées, références des traces, incidents, ablations, SHA des commits et limites connues doivent être consignés pour toute exécution réelle.

## 9. Limites

- Mode démo = test d'orchestration, pas qualité LLM.
- Pas de mesure réelle sans exécution traçable.
- Pas de données sensibles/patients dans les traces.
- Les validateurs `valid_schema`/`grounded`, les contrôles de transfert et le garde-fou budgétaire sont implémentés et testés localement ; ils ne valident pas le contenu métier et restent à faire ratifier en revue avant usage réel.

### Frontière des preuves

- Les exécutions locales d'Omar (Windows/Python 3.12.10) et la CI vérifient le **logiciel** : imports uniques, tests unitaires, orchestration démo. Elles ne produisent aucun résultat LLM.
- Les cas et évaluations **RCS-81** ne sont pas gelés collectivement ; aucune comparaison TP04/TP05 ne doit être annoncée comme validée avant gel par commit et revue humaine.
- Un mock est acceptable pour tester le logiciel, **jamais** pour mesurer la qualité des modèles ou étayer un GO/NO-GO.
