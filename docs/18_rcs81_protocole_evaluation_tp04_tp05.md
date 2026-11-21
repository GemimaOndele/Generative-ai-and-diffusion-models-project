# RCS-81 — Protocole commun TP04 ↔ TP05 : évaluateur exécutable

**Pilote : Gémima ; binôme : Aminata ; relais : Omar ; relecteur : Elias.**  
**Statut : outillage et tests préparés, scénario non gelé et zéro exécution LLM réelle démontrée.** Le TP05 est un complément du J2, pas un troisième jalon.

## Unité fonctionnelle candidate (à approuver)

Une **demande documentaire liée à une maintenance simulée** est considérée correctement traitée lorsque le modèle donne une réponse fidèle à une source autorisée **ou** s'abstient/refuse correctement (source absente, contradiction ou information sensible). Cela exclut toute réparation, diagnostic patient ou commande autonome.

Règle de réussite métier `pass/fail` définie par la grille gelée ; juger citations/fidélité séparément. Les choix et catégories des dix cas sont proposés et ne sont **pas** encore approuvés.

## Cas communs et quatre stress
- T01–T04 : questions usuelles fictives ;
- T05–T06 : combinaison et qualité de sources ;
- T07 : absence de preuve documentaire ;
- T08 : sources contradictoires ;
- T09 : injection indirecte dans un document ;
- T10 : confidentialité et refus.

Fichier `planning/rcs81_case_manifest.csv` : **tous les cas sont `pending`**, et leur `freeze_commit` est vide. Il faudra les réviser avec Aminata, choisir un corpus autorisé, puis les geler **ensemble** via un commit Git identifié — pas sur la seule décision d'un script. La PR #2 contient une grille de scénarios fictifs à harmoniser avec cette proposition.

## Évaluation réelle attendue
Trois stratégies sur le **même jeu gelé T01–T10** :
1. **mono-A** : LLM A réel, ID/version/permissions vérifiés ;
2. **mono-B** : LLM B réel et distinct, ID/version/permissions vérifiés ;
3. **V2** : routing ou cascade A/B, raison de route enregistrée sur chaque cas.

Chaque ligne de `planning/rcs81_runs_template.csv` doit renseigner modèle, version, `execution_mode=live`, jugement humain `pass/fail`, preuve/trace, durée, coût s'il est réellement connu, citation et raison du routage V2. Un *mock* est acceptable pour tester le logiciel, **jamais** pour un benchmark LLM. Le nom `live` ne suffit pas à prouver l'exécution : les traces doivent être relues.

## Lancer l'outil dans Cursor ou un terminal

```bash
python -m tools.rcs81_evaluate
python -m unittest discover -s tests -p 'test_rcs81_tp05.py' -v
```

Avec les fichiers fournis, la première commande retourne **BLOCKED / cases_not_frozen**, ce qui est le résultat attendu et correct.

Après gel et enregistrement d'une comparaison réellement exécutée :

```bash
python -m tools.rcs81_evaluate --manifest planning/rcs81_case_manifest.csv --results planning/rcs81_runs_template.csv
```

Le calculateur renvoie qualité métier (succès/10), latence p95 (méthode nearest rank), citations et coût total/€/succès **si les dix coûts sont renseignés**. L'énergie du fournisseur LLM distant est ND : elle n'est pas calculée depuis les coûts ou tokens.

Il ne décide jamais GO/NO-GO seul : revue humaine obligatoire sur cas sensibles, risques et coûts.

## C3, TP04 et TP05 : frontières à maintenir
- **C3/60 min** : diffusion (un modèle réellement génératif) et baseline sur son jeu de données. Autre protocole, autre modalité que les documents TP04.
- **TP04/120 min + 30 min optionnelles** : comparer deux véritables LLM et un orchestrateur V2 sur dix cas gelés.
- **TP05/90 min** : reprendre **exactement** cette comparaison pour FinOps, Green AI, trois risques éthiques et au moins un test traçable.

## Suite à réaliser en équipe
- Aminata : relire les dix catégories et les comportements attendus ;
- Elias : justifier modèles A/B, stratégie V2, limites et coût des API ;
- Omar : vérifier les agrégats, unités, référentiel et coûts ;
- Gémima : faire adopter l'unité fonctionnelle, tenir le registre de décision et suivre la PR.

**Aucun jeu clinique ni donnée sensible ne doit figurer sur le dépôt public.** Le fait que la CI réussisse ne vaut ni audit FinOps final, ni comparaison scientifique exécutée.

## Vérification locale du 21 novembre 2026

Exécution Windows / Python 3.12.2 : les six tests initiaux réussissent.
Quatre nouveaux tests de régression reproduisent cinq échecs avant correction :
espaces autour de `pass`/`verified` non comptabilisés, même modèle A/B déguisé
par des espaces, versions variables au sein d'une baseline, et modèle/version
V2 absent des baselines. Le parseur normalise désormais les champs avant
validation ET agrégation ; la comparaison impose une version par baseline et
la réutilisation de leurs identités modèle/version par V2.

Après correction : `python -m unittest discover -s tests -v` → 10 tests réussis.
`python -m tools.rcs81_evaluate` → `BLOCKED / cases_not_frozen`, toujours attendu.
Aucun cas n'a été gelé, aucun appel LLM ni benchmark réel n'a été produit.
Les fixtures des tests restent des fixtures logicielles ; aucune approbation
scientifique ne peut en être déduite. La revue des modèles/traces demeure humaine.
