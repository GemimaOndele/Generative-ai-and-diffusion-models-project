# RCS-62 — Routage Multi-LLM : protocole et acceptation (démo)

> Décision live : **NO_GO**. Ce rapport valide uniquement l'orchestration avec clients simulés ; aucune mesure de qualité LLM n'est produite.

## Politique de sélection et garde-fous

- Routage explicable fondé sur la **catégorie** du cas uniquement : `usual` → A, `complex` → B, `sensitive` → refus avant tout appel.
- Le champ `expected_behavior` est réservé au scoring hors ligne et ne participe jamais au routage.
- Repli (fallback) A→B disponible dans `Orchestrator.run_cascade()` ; bloqué si le transfert vers B n'est pas autorisé.
- `max_calls_per_case = 2`, `allow_paid_calls = false`, budget réservé avant appel, traces minimisées (hash de prompt, sans donnée patient).

## Comparaison sur trois cas (mono-A / mono-B / routage)

| Cas | Catégorie | Route attendue | Route observée | mono-A | mono-B | Routage | Appels routage |
|---|---|---|---|---|---|---|---:|
| T01 | usual | A | A | ok | ok | ok | 1 |
| T05 | complex | A | B | ok | ok | ok | 1 |
| T10 | sensitive | refus | A | refused | refused | refused | 0 |

## Contrôles

| Contrôle | Résultat |
|---|---|
| deux_modeles_distincts | OK |
| selection_par_categorie_uniquement | OK |
| cas_sensible_refuse_sans_appel | OK |
| comparaison_mono_presente | OK |
| traces_sans_secret_ni_expected | OK |
| garde_fous_actifs | OK |

**Porte démo : PASS — décision live : NO_GO.**

## Bloquants avant une exécution réelle

- Modèles A/B réels non validés (licence, droits, région, rétention).
- Cas TP04 non gelés collectivement (freeze_commit vide dans planning/rcs81_case_manifest.csv).
- Aucune mesure de qualité, latence, coût ou énergie en mode démo.

## Reproduction

```bash
python -m tools.rcs62_routing_acceptance --write
python -m tools.rcs62_routing_acceptance --check
python -m unittest tests.test_rcs62_routing_acceptance -v
```

Références : RCS-62, RCS-75 (`src/orchestrator.py`, `tests/test_orchestrator.py`), RCS-81 (`planning/rcs81_case_manifest.csv`), `docs/05_tp04_architecture_v2.md`.
