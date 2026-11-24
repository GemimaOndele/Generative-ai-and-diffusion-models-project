# RCS-62 — Routage Multi-LLM : protocole et acceptation (démo)

> Décision live : **NO_GO**. Ce rapport valide uniquement l'orchestration avec clients simulés ; aucune mesure de qualité LLM n'est produite.

## Politique de sélection et garde-fous

- Route **interne** fondée sur la **catégorie** du cas uniquement : `usual` → A, `complex` → B, `sensitive` → A (route sélectionnée).
- Décision **effective** distincte de la route : `usual`/`complex` → exécution, `sensitive` → **refus avant tout appel** (`transfert_bloque_avant_appel = true`).
- Le champ `expected_behavior` est réservé au scoring hors ligne et ne participe jamais au routage.
- Repli (fallback) A→B réellement exécuté par `Orchestrator.run_cascade()` ; bloqué si le transfert vers B n'est pas autorisé.
- `max_calls_per_case = 2`, `allow_paid_calls = false`, budget réservé avant appel, traces minimisées (hash de prompt, sans donnée patient).

## Comparaison sur trois cas (mono-A / mono-B / routage)

| Cas | Catégorie | Route interne attendue | Route sélectionnée | Décision attendue | Décision observée | mono-A | mono-B | Routage | Appels routage |
|---|---|---|---|---|---|---|---|---|---:|
| T01 | usual | A | A | A | ok | ok | ok | ok | 1 |
| T05 | complex | B | B | B | ok | ok | ok | ok | 1 |
| T10 | sensitive | A | A | refus | refused | refused | refused | refused | 0 |

Pour T10, la route sélectionnée reste A : le refus porte sur le transfert, pas sur le choix interne. Aucun appel n'est émis sur `mono-A`, `mono-B`, `routing_a_b` ni `cascade_a_b`.

## Sondes de repli (exécutées)

| Sonde | Statut | Raison | Appels | Décisions |
|---|---|---|---:|---|
| repli_autorise | ok | validated_by_b | 2 | try_a, fallback_to_b |
| repli_refuse | abstain | fallback_blocked | 1 | try_a |
| cas_sensible | refused | transfer_blocked | 0 | try_a |

## Contrôles

| Contrôle | Résultat |
|---|---|
| deux_modeles_distincts | OK |
| selection_par_categorie_uniquement | OK |
| route_effective_conforme_au_rapport | OK |
| cas_sensible_refuse_sans_appel | OK |
| fallback_autorise_effectif | OK |
| fallback_refuse_sans_appel_b | OK |
| comparaison_mono_presente | OK |
| traces_sans_secret_ni_expected | OK |
| garde_fous_actifs | OK |

**Porte démo : PASS — décision live : NO_GO.**

## Bloquants avant une exécution réelle

- Modèles A/B réels non validés (licence, droits, région, rétention).
- Cas TP04 non gelés collectivement (freeze_commit vide dans planning/rcs81_case_manifest.csv).
- Aucune mesure de qualité, latence, coût ou énergie en mode démo.
- Le mode démo valide l'orchestration, jamais la qualité des modèles. La route interne sélectionnée n'est pas la décision effective : un cas sensitive reste routé vers A mais est refusé avant tout appel.

## Reproduction

```bash
python -m tools.rcs62_routing_acceptance --write
python -m tools.rcs62_routing_acceptance --check
python -m unittest tests.test_rcs62_routing_acceptance -v
```

Références : RCS-62, RCS-75 (`src/orchestrator.py`, `tests/test_orchestrator.py`), RCS-81 (`planning/rcs81_case_manifest.csv`), `docs/05_tp04_architecture_v2.md`.
