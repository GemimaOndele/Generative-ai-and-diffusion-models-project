# Readiness d'exécution — Priorités Elias

> État au 2026-11-23, après rebase sur le socle `main` (`bd1c5d1`). Aucun résultat réel inventé. Les exécutions live sont bloquées par les autorisations, les données et l'accès aux modèles. Les seules vérifications faites sont locales (Omar, Windows/Python 3.12.10) et logicielle en mode démo.

## RCS-61 / RCS-62 / RCS-75 / RCS-79 — Multi-LLM TP04

| Élément | Statut | Preuve / fichier | Blocage restant |
|---|---|---|---|
| Orchestrateur mono/routing/cascade | Prêt (démo), un seul `src/` | `src/orchestrator.py`, `src/model_config.py` | Défaut V1 à prouver avant choix final |
| Runner benchmark + scoring auto | Prêt (démo), un seul `tests/` | `src/run_benchmark.py`, `src/scoring.py`, `tests/` | — |
| Jeu pédagogique TP04 | Proposé, non gelé | `experiments/tp04_cases.jsonl` | Gel collectif RCS-81 (`freeze_commit` vide) |
| Gabarit vide du socle | Préservé | `experiments/test_cases.jsonl` | Doit rester vide |
| Config live | Gabarit sans secret | `config/tp04_models.example.json` | Renseigner modèles/version/licence/droits/région/rétention |
| Grille scoring pré-écrite | À créer | `src/scoring.py` (règle simple versionnée) | Validation équipe avant live |
| Smoke test démo + CI | Exécuté (30 tests verts) | `.github/workflows/tp04-tests.yml` | Pas une preuve qualité LLM |
| Défaut V1 observé | ND | `docs/05_tp04_architecture_v2.md` | Besoin traces/résultats V1 |
| Modèles A/B autorisés | ND | — | Nom/version/fournisseur/licence/région/rétention/coût + approbation budget |
| Exécution live | Bloqué | — | `--confirm-paid-calls` seulement après autorisations |
| Décision GO/NO-GO | ND | `docs/05_tp04_benchmark.md` | Après mesures réelles |

## RCS-55 — Baseline règles/ML

| Élément | Statut | Preuve / fichier | Blocage restant |
|---|---|---|---|
| Script baseline | Prêt | `experiments/baseline_rules_ml.py` | — |
| Notebook | Prêt | `experiments/baseline_rules_ml.ipynb` | — |
| Smoke test synthétique | Possible | commande `--synthetic` | Pas preuve médicale |
| Dataset autorisé | ND | `data/manifest.md` | Provenance/licence/droits/sensibilité |
| Exécution réelle + métriques | Bloqué | — | Dataset autorisé |
| Consignation manifest/splits | Gabarit prêt | `data/manifest.md` | À remplir après run |

## RCS-57 / RCS-70 — Diffusion J1

| Élément | Statut | Preuve / fichier | Blocage restant |
|---|---|---|---|
| POC diffusion 1D | Prêt (smoke) | `experiments/diffusion_poc.py` | — |
| Config exemple | Prêt | `experiments/diffusion_config.example.json` | — |
| Étude Diffusion-TS/PhysDiff | Brouillon | `docs/06_etude_diffusion_ts_physdiff.md` | Vérifier licences/repos |
| Smoke test synthétique | Possible | `--synthetic --epochs 2` | Pas preuve médicale |
| Dataset J1 autorisé | ND | — | Données/provenance/licence/GPU |
| Exécution réelle + artefacts | Bloqué | — | Dataset + infra + protocole validé |
| Comparaison baseline vs diffusion | ND | — | Mêmes cas figés, métriques définies |

## RCS-85 / RCS-88 — TP05 / Gouvernance

| Élément | Statut | Preuve / fichier | Blocage restant |
|---|---|---|---|
| Template TP05 FinOps/Green/Éthique | Prêt | `docs/06_tp05_finops_green_ethique.md` | Mesures réelles |
| CSV mesures TP05 | Gabarit ND | `experiments/results/tp05_mesures.csv` | Exécutions réelles |
| Model/dataset cards + biais | Gabarit | `docs/08_model_cards_dataset_cards_biais.md` | Données/systèmes réels, tests |
| Registre risques/ADR | Gabarit | `docs/registre_decisions_risques.md` | Ratification équipe |

## Commandes de vérification

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m src.run_benchmark --mode demo --cases experiments/tp04_cases.jsonl --out experiments/results/tp04_demo
python experiments/baseline_rules_ml.py --synthetic --out experiments/results/baseline_rules_ml_synthetic.json
python experiments/diffusion_poc.py --synthetic --epochs 2 --out experiments/results/diffusion_poc.json
```
