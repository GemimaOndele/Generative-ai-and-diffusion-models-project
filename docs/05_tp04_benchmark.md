# TP04 — Benchmark et décision · RCS-77 à RCS-79

**État : gabarit vierge, résultats non mesurés.**

## Protocole
10 cas gelés : T01–T04 usuels, T05–T06 complexes, T07 source absente, T08 source contradictoire, T09 injection indirecte, T10 information sensible/hors périmètre. Évaluer mono-A, mono-B, routing A/B, cascade A→B sur les **mêmes** cas.

## Tableau de synthèse
| Stratégie | Score / qualité | p50, p95 | Coût/cas | Échec/refus | Citations |
|---|---|---|---|---|---|
| mono-A | NM | NM | NM | NM | NM |
| mono-B | NM | NM | NM | NM | NM |
| routing A/B | NM | NM | NM | NM | NM |
| cascade A→B | NM | NM | NM | NM | NM |

*NM = non mesuré, et non égal à zéro.* Mesurer qualité métier séparément de la fidélité aux sources. Distinguer coûts de routage, validation, retries et supervision humaine si connus.

## Green AI
Énergie mesurée localement / estimée avec hypothèses / non disponible. CO₂e non déductible du coût API seul. Préciser énergie, PUE, intensité carbone, unité et périmètre commun.

## GO / NO-GO
Décision à prendre **après** résultats. Motifs de refus possibles : dégradation sur cas critiques, transfert interdit, coût ou p95 dépassé, réponses dangereuses.

## Reproductibilité
Versions, commandes, références des traces, incidents, ablations, SHA des commits et limites.
