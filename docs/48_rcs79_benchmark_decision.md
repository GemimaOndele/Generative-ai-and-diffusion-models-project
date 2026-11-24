# RCS-79 — Benchmark V2 Multi-LLM et décision traçable

> Ce document est généré à partir de preuves strictement validées. Sans gel RCS-81 ni modèles conformes, la décision est **NO_GO** ; avec des preuves conformes mais sans vérification humaine externe documentée, elle reste **A_TESTER**. La revue indépendante n'est qu'une déclaration : aucune chaîne de signature n'est vérifiée ici et aucune recommandation ne peut être émise sans vérification humaine et ratification collective. Aucune valeur n'est simulée.

## Comparatif mono / V2

| Stratégie | Qualité (fraction) | p95 (ms) | Coût (€) | CO₂e (kg) | Statut énergie |
|---|---:|---:|---:|---:|---|
| mono-A | ND | ND | ND | ND | ND |
| mono-B | ND | ND | ND | ND | ND |
| V2 | ND | ND | ND | ND | ND |

## Portes de décision

| Contrôle | Résultat |
|---|---|
| cas_geles | BLOQUÉ |
| modeles_ab_valides | BLOQUÉ |
| resultats_live_reels | BLOQUÉ |
| preuves_manifeste_config_run | BLOQUÉ |
| seuils_approuves_avant_resultats | BLOQUÉ |
| declaration_revue_independante | BLOQUÉ |
| commit_reference | BLOQUÉ |
| verification_humaine_externe_signature | BLOQUÉ |
| autorisation_collective | BLOQUÉ |
| qualite_v2_superieure | BLOQUÉ |
| latence_conforme | BLOQUÉ |
| cout_conforme | BLOQUÉ |
| energie_documentee | BLOQUÉ |

**Décision : NO_GO** — relecteur : ND — commit : ND.

## Schémas et bornes exigés

- Résultats : `rcs79_live_results/v1` ; modèles : `rcs79_models/v1` ; revue : `rcs79_independent_review_declaration/v2`.
- Numériques : types JSON uniquement, booléens refusés, finis, ≥ 0 et bornés (qualité et delta ∈ [0, 1] ; p95 ≤ 86 400 000 ms).
- Preuves : hash du manifeste, hash de config, `run_id`, commit complet, dix `case_id`/`freeze_commit`, approbation des seuils avant `executed_at` et déclaration de revue indépendante (relecteur absent des auteurs). Le champ `declaration` n'est pas vérifié cryptographiquement : une signature textuelle ne lève pas la porte `verification_humaine_externe_signature`.

## Limites et bloquants

- Cas RCS-81 non gelés collectivement : freeze_commit absent ou invalide.
- Modèles A/B non conformes : schéma strict, identités canoniques, licence/droits/région/rétention, preuve de validation, manifeste commun et hash de config requis.
- Résultats live non conformes : dix cas et empreintes du manifeste, run, commit, config, valeurs finies bornées et schéma strict exigés.
- Preuves non liées au même manifeste/config/run/commit.
- Seuils approuvés absents, non sourcés ou approuvés après l'exécution.
- Déclaration de revue indépendante absente ou non conforme : rôle indépendant, relecteur absent des auteurs, date et commit requis.
- Vérification humaine externe de la revue non documentée : une déclaration ou une chaîne de signature textuelle n'est pas une preuve vérifiable.
- Commit de référence absent, tronqué ou différent de celui du run.
- Gain V2 inférieur au seuil approuvé ou donnée invalide.
- p95 V2 supérieure au seuil approuvé ou donnée invalide.
- Coût V2 supérieur au seuil approuvé ou donnée invalide.
- Énergie/CO₂e non documentée ou non calculée sur un périmètre commun.
- Autorisation collective non vérifiée : l'outil ne peut émettre qu'une recommandation à ratifier par l'équipe, jamais un GO.
- T01: non gelé
- T01: référence de gel absente ou SHA complet invalide
- Aucune décision GO automatisée. Une déclaration de revue n'est pas une signature vérifiée : la vérification humaine externe et l'autorisation collective restent à documenter, donc au mieux A_TESTER dans cet outil. Un mock ou le mode démo ne peut jamais étayer une recommandation.

## Preuves et reproduction

- `docs/05_tp04_benchmark.md`
- `data/manifest.md`
- `planning/rcs81_case_manifest.csv`
- `README.md`

```bash
python -m tools.rcs79_benchmark_decision --write
python -m tools.rcs79_benchmark_decision --manifest <manifeste_gelé.csv> --models <modeles.json> --results <resultats_live.json> --review-declaration <declaration.json> --reviewer <nom> --commit <sha40|sha64> --write
python -m tools.rcs79_benchmark_decision --check
python -m unittest tests.test_rcs79_benchmark_decision -v
```

Le rapport complète `docs/05_tp04_benchmark.md` et le protocole RCS-81, sans remplacer la ratification collective ni le gel des cas.
