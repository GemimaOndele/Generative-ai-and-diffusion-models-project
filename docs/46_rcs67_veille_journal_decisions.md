# RCS-67 — Veille scientifique et journal de décisions

> Les fiches ci-dessous reprennent uniquement des références déjà citées dans le dépôt ou les tickets. `date_lecture = ND` : aucune lecture récente ni conclusion scientifique n'est inventée.

## Fiches datées

| ID | Référence | Date de citation dans le dépôt | Domaine | Limites | Alternatives | ADR |
|---|---|---|---|---|---|---|
| V-01 | CM03 — première preuve GenAI (ND) | 2026-11-14 | cadrage pédagogique | support de cours; aucune validation clinique | règles/ML; diffusion J1 | ADR-002 |
| V-02 | TP04 — du POC V1 à une V2 Multi-LLM démontrable (ND) | 2026-11-17 | orchestration LLM | défaut V1 non prouvé; modèles A/B et seuils ND | mono-LLM; routing A/B; cascade A→B | ADR-003, ADR-004 |
| V-03 | TP05 — FinOps, Green AI & Éthique (ND) | 2026-11-20 | coût, énergie, éthique | exercice non exécuté; statut ND tant que non mesuré | API distante; calcul local; hybride | ADR-002, ADR-009 |
| V-04 | CodeCarbon — documentation officielle (https://docs.codecarbon.io/latest/) | 2026-11-20 | mesure énergie locale | ne mesure pas l'énergie d'un serveur distant; estimation selon le matériel | mesure locale; API non instrumentée; ND | ADR-002, ADR-009 |
| V-05 | FinOps Foundation — AI FinOps (https://www.finops.org/wg/finops-for-ai-overview/) | 2026-11-20 | gouvernance des coûts | cadre général; aucun tarif du projet n'est fourni | coût API seul; coût complet | ADR-009 |
| V-06 | Green Software Foundation — SCI-AI (https://greensoftware.foundation/standards/sci-ai/) | 2026-11-20 | intensité carbone | modèle d'estimation; périmètre commun à expliciter | SCI; mesure directe; ND | ADR-002 |
| V-07 | CNIL — fiches pratiques IA (https://www.cnil.fr/fr/les-fiches-pratiques-ia) | 2026-11-20 | données et conformité | un audit technique n'est pas une preuve de conformité; revue juridique requise | minimisation; anonymisation; revue juridique | ADR-007 |
| V-08 | Registre des décisions et risques (RCS-18) (ND) | 2026-11-23 | gouvernance projet | la plupart des ADR sont proposés ou à décider; non ratification collective | proposé; accepté; rejeté | ADR-001, ADR-006, ADR-008 |

## Journal ADR ↔ fiches

| ADR | Statut dans le registre | Fiches liées |
|---|---|---|
| ADR-001 | Proposé | V-08 |
| ADR-002 | Proposé | V-01, V-03, V-04, V-06 |
| ADR-003 | Proposé — en attente de validation | V-02 |
| ADR-004 | Proposé (principe) — à confirmer par benchmark | V-02 |
| ADR-006 | À décider | V-08 |
| ADR-007 | À décider | V-07 |
| ADR-008 | À décider | V-08 |
| ADR-009 | À décider | V-03, V-04, V-05 |

## Contrôles

| Contrôle | Résultat |
|---|---|
| fiches_dates_et_sources | OK |
| limites_et_alternatives_presentes | OK |
| adr_ids_existants | OK |
| traceabilite_bidirectionnelle | OK |
| pas_de_date_lecture_inventee | OK |

**Traçabilité : OK — décision scientifique : ND.**

## Reproduction

```bash
python -m tools.rcs67_veille --write
python -m tools.rcs67_veille --check
python -m unittest tests.test_rcs67_veille -v
```

Sources : `governance/adr_register.csv`, `docs/registre_decisions_risques.md`, `docs/06_tp05_finops_green_ethique.md`, tickets RCS-62 à RCS-90.
