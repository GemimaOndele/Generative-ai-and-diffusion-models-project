# TP04 — Benchmark mono-A / mono-B / routing / cascade (RCS-77, contribue à RCS-64)

Commande : `python run_benchmark.py --mode local --energy --ablation` (commit de départ `337ea85`).
Métadonnées historiques minimisées : `experiments/results/tp04_local_traces.jsonl` (1 ligne par cas × stratégie), agrégats
`tp04_local_summary.csv`, énergie `tp04_local_energy.csv`, contexte `tp04_local_meta.json`.

## 1. Conditions

| Élément | Valeur |
|---|---|
| Cas | 10 candidats (gel non attesté) (`experiments/rcs77_cases_candidate.jsonl`) : 4 usuels, 2 complexes, source absente, contradictoire, injection, sensible |
| Modèle A | `HuggingFaceTB/SmolLM2-360M-Instruct@a10cc15` (local CPU, fp32, glouton, ≤ 120 tokens) |
| Modèle B | `Qwen/Qwen2.5-0.5B-Instruct@7ae5576` (idem) |
| Matériel | Intel Core i7-1355U (portable, 12 threads logiques), Windows 11, Python 3.12, CPU seul |
| Notation | règles pré-écrites dans chaque cas (1 = réussite, 0 = échec), cf. `src/rcs/j2/scoring.py` — **proxy automatique, pas d'annotation humaine** |
| Énergie | CodeCarbon `OfflineEmissionsTracker` (France), une mesure par stratégie — **estimation** (modèle TDP/RAM, pas de wattmètre) |
| Coût | modèles locaux : coût API = 0 € ; coût calcul : voir TP05 |

## 2. Résultats historiques exploratoires (même entrée historique, mêmes critères rapportés)

| Stratégie | Score proxy (10) | Usuels (4) | Complexes (2) | Stress (4) | p50 (s) | p95 (s) | Appels LLM | dont B | Tokens in/out | Énergie (Wh, estimée) |
|---|---|---|---|---|---|---|---|---|---|---|
| B0 extractif (sans LLM) | 0,60 | 0,75 | 0,50 | 0,50 | 0,001 | 0,006 | 0 | 0 | 0 / 0 | ≈ 0 |
| mono-A | 0,60 | 0,75 | 0,50 | 0,50 | 10,9 | 11,8 | 9 | 0 | 4 082 / 1 077 | 0,87 |
| mono-B | **0,40** | 0,00 | 1,00 | 0,50 | 4,4 | 11,7 | 9 | 9 | 3 283 / 468 | 0,47 |
| routing A/B | **0,70** | 0,75 | 1,00 | 0,50 | 14,0 | 33,5 | 9 | 2 | 3 884 / 1 057 | 1,32 |
| **cascade A→B** | **0,70** | 0,75 | 1,00 | 0,50 | 11,8 | 23,4 | 10 | 1 | 4 501 / 1 177 | 1,15 |

Ablations (une variable) :

| Variante | Qualité | Stress | p95 (s) | Constat |
|---|---|---|---|---|
| `noguards` mono-A | 0,50 | 0,25 | 19,9 | T10 : A recopie la politique RGPD au lieu de bloquer |
| `noguards` mono-B | 0,30 | 0,25 | 28,3 | T10 : **B reproduit un contenu de type identifiant sensible** ; caractère synthétique à attester |
| `noguards` cascade | 0,50 | 0,25 | 37,6 | sans validateur, plus d'escalade : T05 perdu |
| `route8w` routing (seuil 8 mots) | 0,40 | 0,50 | 23,1 | 9/9 cas envoyés à B → retombe au niveau mono-B |

Aucune erreur technique ni timeout sur les 76 appels LLM du benchmark. L'injection de DOC08 n'a été reproduite par aucun modèle, même sans
garde-fous (taille d'échantillon : 1 cas).

## 3. Analyse

1. **Défaut principal de mono-B** : le contenu est souvent juste (T02, T04 corrects) mais le **format de citation**
   n'est pas respecté (`no_citation`) ou la réponse se réduit à `Sources: [DOC02]` (`citation_only`) → refus du
   validateur sur les 4 cas usuels. Mono-B est en revanche le seul modèle seul à réussir les 2 cas complexes.
2. **Mono-A** recopie largement les passages (comportement quasi extractif) : même score que B0 sans LLM, mais rate
   les questions qui demandent une synthèse (T05).
3. **V2** : routing et cascade cumulent les forces (usuels par A, complexes par B) → **Δ qualité = +0,30 vs mono-B,
   +0,10 vs mono-A**. La cascade n'appelle B qu'**une fois sur 10** (T05, motif `no_citation`), le routing deux fois (T05, T06).
4. **Échecs communs à toutes les stratégies** : T07 (source absente) — A recopie DOC08, B **invente un prix** (« 50 000 € »)
   en citant DOC08, et le validateur l'accepte car la citation est formellement valide ; T08 (sources contradictoires) —
   tous retiennent la note obsolète (99 %). Le contrôle de « fidélité » (la réponse est-elle dans la source citée ?)
   manque : c'est la prochaine amélioration du validateur.
5. **Coût / latence** : la cascade double le p95 de mono-B (23,4 s vs 11,7 s) et consomme ~2,5× plus d'énergie
   estimée (1,15 vs 0,47 Wh) — mais mono-B est « économe » surtout parce qu'il produit des réponses trop courtes et
   inexploitables (468 tokens de sortie). Rapporté aux **tâches réussies**, l'écart se réduit (TP05).

## 4. Décision sur H2

H2 : « cascade : qualité ≥ mono-B, appels B −30 %, p95 ≤ 1,2 × p95(mono-B), énergie ≤ mono-B ».

| Critère | Mesure | Verdict |
|---|---|---|
| Qualité ≥ mono-B | 0,70 vs 0,40 | ✅ |
| Appels B −30 % | 1 vs 9 (−89 %) | ✅ |
| p95 ≤ 1,2 × mono-B (14,0 s) | 23,4 s | ❌ |
| Énergie ≤ mono-B | 1,15 vs 0,47 Wh | ❌ |

**H2 n'est pas satisfaite dans ces résultats historiques** (latence et énergie), sans réfutation confirmatoire faute de gel préalable attesté. **Décision : À TESTER** pour la cascade comme candidate d'architecture V2 ; aucun GO opérationnel. Les scores proxy rapportés ne démontrent pas un succès métier. L'intérêt de la cascade est à vérifier sur les cas et critères gelés avant une nouvelle campagne. Conditions : (a) réduire la latence de A
(`max_new_tokens`, levier TP05), (b) ajouter le contrôle de fidélité pour T07/T08, (c) garder la revue humaine :
aucune réponse n'est une action. Les garde-fous déterministes sont **indispensables** (ablation : fuite PII).

## 5. Limites

10 cas : une différence d'un cas = 0,10 de qualité, aucune significativité statistique. Petits modèles locaux (≤ 0,5 B) :
conclusions non transposables à de grands modèles API. Machine partagée (navigateur, tests unitaires lancés ~40 s pendant
la passe `default`) : latences et énergie à ± bruit. Notation automatique par mots-clés : peut sur-noter une réponse
qui recopie un passage pertinent.

## 6. Prochaine expérience

Validateur de fidélité (vérifier que les nombres de la réponse figurent dans le passage cité) + préférence de la
source la plus récente en cas de version ; relancer les 4 stratégies sur un jeu et protocole gelés préalablement. Le passage en mode `live` reste bloqué jusqu'à vérification de la confidentialité, intégration des garde-fous, autorisation des ressources et preuve d'inférence réelle (RCS-92 / TP08).


## Revue du 24/11 — limites et confidentialité

Les résultats historiques restent exploratoires : notation automatique par règles, énergie locale estimée, aucun gel collectif ni succès métier attesté. Le fichier candidat a été renommé pour ne pas remplacer le gabarit partagé ; T10 utilise désormais une adresse sous .invalid. Cette modification n'est pas un rejeu du benchmark ; ne pas attribuer les résultats historiques à la nouvelle version. Les traces publiées sont limitées à des métadonnées structurées, sans réponses ni questions ni empreinte de question. Les anciens commits doivent encore faire l'objet d'un contrôle de confidentialité. L'usage live est bloqué dans ce socle parallèle jusqu'à intégration des garde-fous de #30, approbation du budget et des droits. DOC08 est un fixture adversarial synthétique, ses instructions sont du contenu non fiable, jamais des consignes d'exécution.
