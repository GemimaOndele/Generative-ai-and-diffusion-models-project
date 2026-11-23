# RCS-78 — journalisation et audit de traces J2 / Green AI

**Pilote Gémima. Statut : composant de vérification à relire, non intégré dans `main`.**

## Pourquoi ce complément ?

Les branches RCS-77 (Omar) et RCS-81 (Gémima) utilisent des structures de traces et des conventions d'évaluation distinctes. RCS-77 contient des traces de comparaison mono-A/mono-B/routing/cascade ; RCS-81 impose une preuve de gel collectif et une validation humaine de l'évaluation. Cette PR ajoute un **audit des métadonnées** non destructif, sans modifier les données ni importer leurs réponses/prompts dans le rapport.

## Exécution

```bash
python -m unittest discover -s tests -p 'test_rcs78_trace_audit.py' -v
python -m tools.rcs78_trace_audit --input experiments/results/tp04_local_traces.jsonl
```

La seconde commande exige un workspace contenant **les traces de la branche RCS-77 d'Omar** ; elles ne sont pas présentes sur la branche RCS-81. Il faut les obtenir dans un répertoire de revue autorisé, ou intégrer le fichier par une PR dédiée après accord. Ce code **n'a pas encore été exécuté sur l'ensemble des traces réelles RCS-77**.

## Entrées acceptées / sortie

- Entrée : JSONL de traces techniques avec `trace_id`, `case_id`, `strategy`, `status`, `latency_ms`. Champs supplémentaires acceptés mais **jamais recopiés en clair dans le rapport**.
- Sortie : nombre de traces, couverture des cas par stratégie/variante, statut d'exécution, latence p95 calculée sur les métadonnées non négatives, disponibilité des scores proxy et modèles, couverture des coûts, doublons et avertissements. Les catégories d'incidents ne sont pas reproduites depuis les prompts.
- `cost_eur=null` signifie ND, **pas zéro euro**. Une stratégie sans coût complet ne fournit pas de coût par succès.
- Les scores `score=1/0` de RCS-77 sont des **scores automatiques proxy**, pas la grille de jugement humain exigée pour une validation RCS-81.
- Les émissions et énergies LLM distantes restent **ND** sans source mesurée ; ce script ne calcule pas d'empreinte carbone à partir du nombre de tokens.
- Le rapport ne contient jamais les champs `answer`, `question`, `raw_prompt`, `api_key` ni de texte issu de ces champs.

## Points à faire valider

1. **Omar** : vérifier mapping des champs, `variant`, les critères de qualité et les numéros de cas réels RCS-77 ; relier les références exactes des commits/manifests.
2. **Elias** : confirmer les modèles et versions A/B, évaluer l'abstention T07/T08, les tests d'injection et les stratégies.
3. **Aminata** : vérifier unité fonctionnelle et interprétation métier, absence d'automatisation médicale.
4. **Gémima** : rapprocher les traces des tâches RCS-81/90 et des registres de coûts, puis actualiser l'état Jira.
5. **Ayoub** : vérifier la CI et l'intégration une fois la PR de socle #1 approuvée.

## Restrictions et décisions

Aucune commande à un appareil médical et aucune donnée patient ne doit apparaître dans ce dépôt. Les traces peuvent comporter des textes sensibles ; le rapport n'affiche que des **indicateurs de couverture** et alerte sur les noms de champs sensibles. L'absence de champ sensible ne prouve pas l'absence de donnée sensible dans les valeurs ; **une revue du corpus source reste obligatoire**.

Cette PR est **empilée sur la branche RCS-81**. Elle ne doit pas être fusionnée vers `main` directement. La PR #1 doit d'abord être approuvée et les divergences des schémas de résultats résolues.
