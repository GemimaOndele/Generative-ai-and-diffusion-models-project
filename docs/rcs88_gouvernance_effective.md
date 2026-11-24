# RCS-88 — Gouvernance effective des modèles et jeux de données

> Jira : [RCS-88](https://gemimakerenondelepourou.atlassian.net/browse/RCS-88) — *Créer model cards, dataset cards et matrice de biais/robustesse*.
> Suite au commentaire sur la PR #4 fusionnée (`9806306`) : les gabarits existent, les **fiches effectives, le protocole de biais et les preuves** restaient à compléter.

## Ce qui est livré

| Livrable | Emplacement |
|---|---|
| Outil de génération et de contrôle | `tools/rcs88_governance.py` |
| Tests de non-régulation gouvernance | `tests/test_rcs88_governance.py` |
| 4 model cards (baseline, diffusion J1, mono-LLM, V2) | `governance/rcs88/model_card_*.md` |
| 4 dataset cards (D-001, D-001b, D-002, D-003) | `governance/rcs88/dataset_card_*.md` |
| Matrice biais/robustesse | `governance/rcs88/matrice_biais_robustesse.md` |
| Protocole de biais et de refus | `governance/rcs88/protocole_refus_biais.md` |
| Plan d'action avant démo | `governance/rcs88/plan_action.md` |
| Rapport d'acceptation | `governance/rcs88/acceptance.json` |

Les fiches sont dérivées de `data/manifest.md`, des gabarits `governance/model_card_template.md` et `governance/dataset_card_template.md` (PR #4) et de `docs/11_cartographie_risques_biais.md`. Aucune métrique, population, licence ou conclusion d'absence de biais n'est inventée : les champs non établis restent `ND`.

## Règles appliquées

1. **Refus par défaut.** Un sous-groupe absent du manifeste, non autorisé, ou sans preuve (jeu identifié, effectif, métriques, provenance) donne `REFUSED` — « évaluation non disponible ».
2. **Aucun attribut sensible inféré.** Seules cinq dimensions sont recevables : `type_appareil`, `site`, `regime_signal`, `langue`, `format`, et uniquement si les données autorisées le permettent.
3. **Pas d'absence de biais.** Même une évaluation recevable reste sous revue humaine et ne conclut jamais à l'absence de biais.
4. **Démo bloquée sans preuve.** `acceptance.json` reste `NO_GO` tant que `governance/rcs88/proof.json` n'est pas fourni avec un relecteur, une date, une décision et des références de preuve existantes.

## Utilisation

```bash
python tools/rcs88_governance.py --write      # régénère les fiches et le rapport
python tools/rcs88_governance.py --check      # code 1 tant que la démo n'est pas autorisable
python -m unittest tests.test_rcs88_governance -v
```

Format de preuve attendu (à remplir **par un humain**, jamais généré automatiquement) :

```json
{
  "reviewer": "nom du relecteur ayant ratifié la décision",
  "review_date": "AAAA-MM-JJ",
  "decision": "GO | NO_GO | A_TESTER",
  "evidence": ["chemin/vers/un/fichier/existant", "https://exemple/lien/interne"]
}
```

Une preuve signée autorise au plus une démo sous revue humaine : elle ne constitue **ni** une validation clinique, **ni** une autorisation d'action autonome sur un appareil.

## Liens transversaux

RCS-18 (registre des risques), RCS-65/RCS-82 (coûts), RCS-66/RCS-84 (conformité et éthique TP05), RCS-63/RCS-78/RCS-86/RCS-89 (monitoring et traces), RCS-81/RCS-69 (gel des cas). L'attribution proposée (Elias / Aminata / Omar / Gémima) reste à ratifier en équipe.
