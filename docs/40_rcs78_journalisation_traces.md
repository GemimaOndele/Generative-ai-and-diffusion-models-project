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

## Vérification de compatibilité avec la branche RCS-77 (23/11/2026)

Le fichier **exact** `experiments/results/tp04_local_traces.jsonl` de la branche `experiment/RCS-77-comparer-mono-routing-cascade` (blob GitHub SHA `492b853891da93b7d2357aa66f12b060f34b17cf`) a été relu et les **métadonnées agrégées** sans exposer le contenu de `answer` ou des documents. Il comporte **90 traces valides**, 9 groupes stratégie/variante de 10 cas chacun, sans doublon stratégie/variante/cas dans cette version. Les noms des stratégies correspondent aux enums du nouvel auditeur : `b0_extractive`, `mono_a`, `mono_b`, `routing`, `cascade`.

| Groupe | Traces | Modèle signalé dans les traces | p95 observée (ms, nearest rank) |
|---|---:|---:|---:|
| b0_extractive:default | 10 | 0/10 | 8,4 |
| mono_a:default | 10 | 9/10 | 11 841,4 |
| mono_b:default | 10 | 9/10 | 12 622,8 |
| routing:default | 10 | 9/10 | 35 861,1 |
| cascade:default | 10 | 9/10 | 24 615,8 |
| mono_a:noguards | 10 | 10/10 | 22 052,3 |
| mono_b:noguards | 10 | 10/10 | 34 518,6 |
| cascade:noguards | 10 | 10/10 | 38 232,8 |
| routing:route8w | 10 | 9/10 | 32 304,0 |

Les 90 lignes ont un champ de score proxy et **`cost_eur=null`** : couverture coûts manquante **90/90**, pas un prix nul. Les statuts d'exécution sont `ok`. Ces nombres sont une **lecture analytique des métadonnées du fichier source**, pas une nouvelle exécution des LLM, une approbation scientifique, ni la preuve que la CI de cette PR a importé le fichier d'Omar. Les contrôles `model_trace_coverage` ne garantissent pas la vérification des versions de modèle. Les scores du rapport de benchmark RCS-77 peuvent utiliser une méthode d'agrégation de latence différente ; ne pas confondre les deux sans confronter les définitions. La branche RCS-78 n'intègre pas les traces brutes pour éviter toute duplication de réponses pouvant comporter du contenu sensible.

La prochaine validation est une revue conjointe des versions, licences et critères de gel, notamment les cas T07/T08 où la simple présence d'une citation ne garantit pas la fidélité.
