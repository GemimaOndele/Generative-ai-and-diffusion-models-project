# Tests

Les cas d'entrée sont à définir puis figer avant toute évaluation. `cases.csv` et `experiments/test_cases.jsonl` restent volontairement vides (contrat du socle). Les dix cas pédagogiques TP04 proposés sont dans `experiments/tp04_cases.jsonl` ; ils ne sont **pas** les cas gelés RCS-81.

Tests unitaires présents : `test_model_config.py` (identité A/B, droits, budget), `test_orchestrator.py` (mono, cascade, routing, refus), `test_scoring.py` (règle simple, latences/coûts connus), `test_baseline_mono.py` (workload RCS-61, reproductibilité et logs), plus les tests de structure du socle.

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Ces tests vérifient le logiciel et l'orchestration ; un mock ne mesure jamais la qualité d'un LLM.
