# RCS-64 — Comparer qualité, latence, coût et CO₂e du J2

Pilote : Omar · binôme : Elias · relecteur : Ayoub. Rapport de synthèse ; détails dans
`docs/33_rcs77_tp04_benchmark.md` (RCS-77) et `docs/36_rcs82_tp05_finops_green_ethique.md` (RCS-82).

## Conditions comparables

Même workload (10 cas historiques (gel préalable non vérifié) : 4 usuels, 2 complexes, source absente, contradiction, injection, donnée sensible),
règles de notation déclarées pré-écrites (antériorité non attestée), même prompt, même recherche top-3, mêmes garde-fous, même machine
(Intel i7-1355U, CPU), décodage glouton (reproductible : 10/10 réponses identiques entre deux passes).
Modèles : A = `HuggingFaceTB/SmolLM2-360M-Instruct@a10cc15`, B = `Qwen/Qwen2.5-0.5B-Instruct@7ae5576` (Apache-2.0, locaux).

## Résultats historiques (rapportés, à reproduire)

**J2 — assistant Multi-LLM** (10 cas historiques (gel préalable non vérifié), 2 LLM ouverts locaux, CPU) :

| Stratégie | Score proxy | p95 | Appels B | Énergie estimée | € élec./score positif (hyp. 0,25 €/kWh) |
|---|---|---|---|---|---|
| B0 extractif (sans LLM) | 0,60 | 0,0058 s | 0 | ≈ 0 | ≈ 0 |
| mono-A SmolLM2-360M | 0,60 | 11,8 s | 0 | 0,87 Wh | 0,000036 |
| mono-B Qwen2.5-0.5B (V1) | 0,40 | 11,7 s | 9 | 0,47 Wh | 0,000029 |
| routing A/B | 0,70 | 33,5 s | 2 | 1,32 Wh | 0,000047 |
| **cascade A→B (V2)** | **0,70** | 23,4 s | **1** | 1,15 Wh | 0,000041 |

Décisions : cascade = **candidat GO conditionnel, à arbitrer** (H2 réfutée sur la latence/énergie, mais seule stratégie qui réussit usuels
et complexes) ; levier `max_new_tokens=60` = **rejeté** (qualité 0,70 → 0,40) ; garde-fous indispensables (sans eux, le
modèle B recopie le nom et le NIR d'un patient). Risque résiduel : hallucination sourcée (T07) et source obsolète (T08).

Statuts : qualité = **score proxy automatique, non validé métier** ; p95, appels, tokens = **rapportés comme mesurés** ; énergie = **estimée** (CodeCarbon, TDP, France) ;
€ = **calculé** avec un tarif électrique **hypothétique** ; coût API = 0 € (local, hors coût complet) ; temps de revue humaine = **ND**.

## Robustesse (stress et ablations)

| Test | Constat |
|---|---|
| Donnée sensible (T10) | bloquée avant LLM avec garde-fous ; **sans garde-fous, B recopie nom + NIR** |
| Injection (T09) | aucune charge reproduite (avec ou sans garde-fous ; 1 seul cas) |
| Source absente (T07) | échec général : B **invente un prix** en citant une source réelle |
| Source contradictoire (T08) | échec général : la note obsolète est retenue |
| Seuil de routage abaissé | tout part vers B → qualité retombe à 0,40 |
| `max_new_tokens` 60 | qualité cascade 0,70 → 0,40 ; énergie −11 % seulement → rejeté |

## Limites explicites

10 cas (1 cas = 0,10 de qualité, pas de significativité) ; petits modèles locaux non représentatifs de grands
modèles API ; notation automatique (proxy) ; énergie estimée sans wattmètre ; latence variable jusqu'à ×3 entre deux
passes sur ce portable (comparer seulement à l'intérieur d'une passe) ; amont (entraînement, matériel) hors périmètre.

Sources des chiffres : `experiments/results/tp04_local_*`, `experiments/results/tp05_lever_*`.


## Revue de provenance, confidentialité et CO₂e

Les métadonnées historiques indiquent le commit abrégé `337ea85` ; il ne prouve pas le gel préalable ni les droits d'utilisation. Le gel collectif RCS-81 (#9), la validation des citations et des succès métier restent à établir. Les comparaisons sont exploratoires et ne constituent pas une décision GO. Le coût complet, le temps humain et la CO₂e des API distantes restent ND.

Les traces publiables sont désormais limitées aux métadonnées structurées (identifiants techniques reconstruits, métriques, modèle reconnu). Réponses, questions, raisons libres, extraits et autres contenus bruts ne sont pas copiés. `experiments/results/rcs64_trace_inventory.json` référence les blobs originaux à des fins de provenance ; cette correction ne purge pas l'historique Git. Faire contrôler séparément les éventuelles données sensibles et la politique de conservation avant fusion.

CO₂e locale estimée (kg, CodeCarbon machine) : mono-A 0,00004863 ; mono-B 0,00002608 ; routing 0,00007401 ; cascade 0,00006466. Ces estimations ne sont pas des mesures au wattmètre ni du cycle de vie complet.
