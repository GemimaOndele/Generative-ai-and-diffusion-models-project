# RCS-79 — Benchmark V2 Multi-LLM et décision GO/NO-GO

> Ce document est généré à partir des preuves fournies. Sans gel RCS-81 ni modèles A/B validés, la décision est **NO_GO** ; sans exécution live, elle reste **A_TESTER**. Aucune valeur n'est simulée ici.

## Comparatif mono / V2

| Stratégie | Qualité | p95 (ms) | Coût (€) | CO₂e (kg) | Statut énergie |
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
| qualite_v2_superieure | BLOQUÉ |
| latence_conforme | BLOQUÉ |
| cout_conforme | BLOQUÉ |
| energie_documentee | BLOQUÉ |
| revue_humaine | BLOQUÉ |
| commit_reference | BLOQUÉ |

**Décision : NO_GO** — relecteur : ND — commit : ND.

## Limites et bloquants

- Cas RCS-81 non gelés collectivement : freeze_commit absent ou invalide.
- Modèles A/B réels non validés (identité, licence, droits, région, rétention).
- Aucune exécution live réelle sur dix cas : le mode démo ne mesure pas la qualité.
- Gain V2 inférieur au seuil approuvé ou seuil ND.
- p95 V2 supérieure au seuil approuvé ou seuil ND.
- Coût V2 supérieur au seuil approuvé ou seuil ND.
- Énergie/CO₂e non documentée ou non calculée sur un périmètre commun.
- Relecteur humain absent.
- Commit de référence absent.
- T01: non gelé
- T01: référence de gel absente ou SHA complet invalide
- Un mock ou le mode démo ne peut jamais étayer un GO.

## Preuves et reproduction

- `docs/05_tp04_benchmark.md`
- `data/manifest.md`
- `planning/rcs81_case_manifest.csv`
- `README.md`

```bash
python -m tools.rcs79_benchmark_decision --write
python -m tools.rcs79_benchmark_decision --manifest <manifeste_gelé.csv> --models <modeles.json> --results <resultats_live.json> --reviewer <nom> --commit <sha> --write
python -m tools.rcs79_benchmark_decision --check
python -m unittest tests.test_rcs79_benchmark_decision -v
```

Le rapport complète `docs/05_tp04_benchmark.md` et le protocole RCS-81, sans remplacer la revue humaine ni le gel collectif des cas.
