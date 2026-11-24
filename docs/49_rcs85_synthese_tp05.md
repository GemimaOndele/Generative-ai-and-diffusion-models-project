# RCS-85 — Synthèse TP05 (coût, émissions, risques, décision)

> Décision : **À TESTER**. Source chiffrée unique : `experiments/results/tp05_mesures.csv` (0 ligne(s), SHA-256 `b6f5cb5177cf…`). Aucune valeur n'est inventée.

## Coût par tâche réussie et source

| Stratégie | Cas | Succès | Coût variable (€) | Coût alloué (€) | Coût/succès (€) | Statut | Source / date |
|---|---:|---:|---:|---:|---:|---|---|
| mono-A | 0 | ND | ND | ND | ND | ND | ND / ND |
| mono-B | 0 | ND | ND | ND | ND | ND | ND / ND |
| V2 | 0 | ND | ND | ND | ND | ND | ND / ND |

## Empreinte Green : état et périmètre

| Stratégie | Énergie (kWh) | CO₂e (kg) | Statut | Frontière |
|---|---:|---:|---|---|
| mono-A | ND | ND | ND | ND |
| mono-B | ND | ND | ND | ND |
| V2 | ND | ND | ND | ND |

API distante non instrumentée par CodeCarbon local ; aucune valeur n'est mise à zéro.

## Risque résiduel

| Risque (personnes touchées) | Test / preuve | Source |
|---|---|---|
| Hallucination ou citation absente (technicien, sécurité du service) | ND | `docs/06_tp05_finops_green_ethique.md` |
| Injection indirecte de document (technicien, équipe sécurité) | ND | `docs/06_tp05_finops_green_ethique.md` |
| Données patient et droits (patients, établissement) | ND | `docs/06_tp05_finops_green_ethique.md` |
| Décision de maintenance autonome (technicien, personnes concernées) | ND | `docs/06_tp05_finops_green_ethique.md` |

Risque principal : **ND**. Un test `ND` signifie non exécuté, pas `PASS`.

## Décision et limites

**À TESTER** — relecteur : ND.

- Aucune valeur n'est inventée : le CSV de mesures sert de seule source chiffrée.
- Coût par succès ND si succès = 0, coût incomplet ou source absente (jamais 0 €).
- Statut énergie = le plus faible des statuts déclarés ; zéro n'est jamais substitué à ND.
- Les tests éthiques ND ne valident aucune conformité RGPD/AI Act.
- La synthèse ne remplace ni la revue humaine ni le gel collectif des cas TP04/TP05.

## Fichiers versionnés et reproduction

- `docs/06_tp05_finops_green_ethique.md`
- `experiments/results/tp05_mesures.csv`
- `docs/49_rcs85_synthese_tp05.md`
- `governance/rcs85/synthese.json`

```bash
python -m tools.rcs85_synthese_tp05 --write
python -m tools.rcs85_synthese_tp05 --reviewer <nom> --write
python -m tools.rcs85_synthese_tp05 --check
python -m unittest tests.test_rcs85_synthese_tp05 -v
```

Complète `docs/06_tp05_finops_green_ethique.md` (section 5) et `docs/05_tp04_benchmark.md`.
