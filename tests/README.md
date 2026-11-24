# Tests

Les cas d'entrée sont à définir puis figer avant toute évaluation. `cases.csv` et `experiments/test_cases.jsonl` restent volontairement vides (contrat du socle). Les dix cas pédagogiques TP04 proposés sont dans `experiments/tp04_cases.jsonl` ; ils ne sont **pas** les cas gelés RCS-81.

Tests unitaires présents : `test_model_config.py` (identité A/B, droits, budget), `test_orchestrator.py` (mono, cascade, routing, refus), `test_scoring.py` (règle simple, latences/coûts connus), `test_baseline_mono.py` (RCS-61 : cinq fixtures de smoke test distinctes du benchmark J2), `test_compare_approaches.py` (RCS-22 : hypothèses et séparation J1/J2), plus les tests de structure du socle.

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Ces tests vérifient le logiciel et l'orchestration ; un mock ne mesure jamais la qualité d'un LLM.
