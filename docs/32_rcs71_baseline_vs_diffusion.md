# RCS-71 — Baseline vs diffusion sur les mêmes cas (C3)

Pilote : Omar · binôme : Elias · relais : Ayoub · relecteur : Gémima.

Commande : `python src/run_j1_diffusion.py` (3 seeds, ~6 min CPU). Résultats bruts : `experiments/results/j1_runs.jsonl`,
agrégats : `j1_summary.csv`, configuration : `j1_config.json`, preuve de génération : `j1_generation.json`.

## 1. Protocole rapporté (chronologie du gel à vérifier)

| Élément | Choix | Justification |
|---|---|---|
| Données | AI4I 2020 (UCI, CC BY 4.0), SHA-256 `dc6630cd…a8e` | seule source licite et accessible ; **substitut NON médical** (cf. `docs/24_rcs40_dictionnaire_contrat_donnees.md`) |
| Tâche | détection d'anomalies non supervisée : score par observation, label = `Machine failure` | les labels ne servent QU'À l'évaluation |
| Split | stratifié 60/20/20, seed 42 figée ; entraînement sur les **normaux du train** (5 797 lignes) | test indépendant (2 000 lignes, 68 pannes) jamais vu |
| Seuil | quantile 95 % des scores des normaux de **validation** (FPR cible 5 %) | ADR-003 ; le test ne sert jamais à régler le seuil |
| Métriques | PR-AUC (principale, classes déséquilibrées 3,4 %), ROC-AUC, rappel et FPR au seuil, F1, rappel par mode de panne, latence | Bibliothèque §10.2 |
| Seeds | 0, 1, 2 (moyenne ± écart-type) ; z-score déterministe | variance d'entraînement |
| Représentations | `raw` = 5 mesures ; `physics` = + ΔT, puissance, usure×couple | facteur testé séparément (connaissance métier explicite) |

Modèles comparés (mêmes entrées, mêmes critères) :

- **B0-a** règle z-score : `max |z|` sur les variables numériques.
- **B0-b** Isolation Forest (200 arbres).
- **G1 DDPM tabulaire conditionnel** (MLP 3×128, T = 100, β linéaire 1e-4→0,02, 4 000 itérations Adam, conditionné sur le type L/M/H), entraîné sur les normaux. Variantes (UN facteur changé à la fois) :
  - **G1-A** score « ELBO » : erreur de débruitage ‖ε − ε_θ(x_t, t)‖² moyennée sur 10 pas × 4 bruits (40 NFE) — référence ;
  - **G1-B** = G1-A avec 3 pas (12 NFE) — ablation coût/latence ;
  - **G1-C** score par reconstruction : bruitage à t0 = 50 puis débruitage ancestral (204 NFE) — ablation fonction de score ;
  - **G1-D** = G1-C avec échantillonneur DDIM 5 pas (20 NFE) — ablation sampler.

## 2. Résultats historiques exploratoires rapportés (test, moyenne sur 3 seeds)

| Repr. | Modèle | PR-AUC | ROC-AUC | Rappel @5 % FPR | FPR test | F1 | ms / 1 000 obs. |
|---|---|---|---|---|---|---|---|
| raw | B0-a z-score | 0,152 | 0,813 | 0,235 | 0,055 | 0,168 | 0,02 |
| raw | B0-b Isolation Forest | 0,069 ± 0,002 | 0,737 | 0,098 | 0,060 | 0,070 | 31 |
| raw | **G1-A DDPM ELBO 10 pas** | **0,236 ± 0,028** | 0,773 | **0,338 ± 0,029** | 0,046 | **0,257** | 111 |
| raw | G1-B ELBO 3 pas | 0,113 ± 0,045 | 0,693 | 0,226 | 0,051 | 0,167 | 39 |
| raw | G1-C reconstruction t0=50 | 0,047 ± 0,003 | 0,566 | 0,078 | 0,058 | 0,058 | 590 |
| raw | G1-D reconstruction DDIM 5 | 0,047 ± 0,012 | 0,535 | 0,088 | 0,059 | 0,063 | 83 |
| physics | **B0-a z-score** | **0,249** | **0,883** | **0,515** | 0,061 | **0,318** | 0,18 |
| physics | B0-b Isolation Forest | 0,133 ± 0,022 | 0,835 | 0,240 | 0,056 | 0,169 | 75 |
| physics | G1-A DDPM ELBO 10 pas | 0,181 ± 0,018 | 0,760 | 0,324 ± 0,015 | 0,052 | 0,231 | 169 |
| physics | G1-B ELBO 3 pas | 0,117 ± 0,030 | 0,689 | 0,216 | 0,044 | 0,177 | 51 |
| physics | G1-C reconstruction t0=50 | 0,045 ± 0,004 | 0,545 | 0,083 | 0,052 | 0,065 | 819 |
| physics | G1-D reconstruction DDIM 5 | 0,051 ± 0,009 | 0,550 | 0,093 | 0,048 | 0,076 | 89 |

Taux de base (classifieur aléatoire) : PR-AUC ≈ 0,034. Entraînement DDPM : ~29 s (raw) / ~55 s (physics) par seed sur CPU.

Rappel par mode de panne (test, au seuil) — extrait :

| Repr. | Modèle | TWF (7) | HDF (26) | PWF (15) | OSF (20) | RNF (5) |
|---|---|---|---|---|---|---|
| raw | B0-a z-score | 0,00 | 0,04 | 0,87 | 0,15 | 0,00 |
| raw | G1-A DDPM | 0,19 | 0,13 | 0,69 | 0,45 | 0,00 |
| physics | B0-a z-score | 0,00 | 0,04 | 1,00 | 1,00 | 0,00 |
| physics | G1-A DDPM | 0,14 | 0,19 | 0,69 | 0,32 | 0,07 |

## 3. Preuve de génération et contrôle de mémorisation (G1-A, seed 0)

2 000 observations « normales » générées par échantillonnage ancestral complet (100 pas) depuis le bruit :
statistiques marginales proches du réel (ex. raw : couple 39,6 ± 8,9 N·m généré vs 39,7 ± 9,5 réel ; KS ≤ 0,07 sur les
5 variables), avec une variance légèrement sous-estimée (rpm : σ 144 vs 167). Contrôle de copie : la distance médiane au
plus proche voisin du train est 0,31 pour les générés vs 0,28 pour de vrais points held-out, et seulement **0,5 %** des
générés sont plus proches du train que le 1er centile des vrais held-out (≈ 1 % attendu sans copie) → **aucun signal de copie détecté par ce contrôle exploratoire**, sans preuve générale d'absence de mémorisation.

## 4. Analyse

1. **Résultat exploratoire favorable sur raw** : sur les mesures brutes, la diffusion (score ELBO) dépasse les deux baselines non génératives :
   PR-AUC 0,236 vs 0,152 (z-score) et 0,069 (Isolation Forest), rappel 0,34 vs 0,24 à FPR ≈ 5 %. Elle détecte des modes
   que la règle rate (OSF 0,45 vs 0,15 ; TWF 0,19 vs 0).
2. **Échec / limite** : avec les variables physiques dérivées, une simple règle z-score devient la meilleure méthode
   (PR-AUC 0,249, rappel 0,51) car AI4I est généré par des règles de seuil sur exactement ces grandeurs (cf. DOC02) :
   l'avantage de la diffusion **disparaît dès que la connaissance métier est explicite**. La fonction de score compte plus
   que le sampler : la reconstruction (G1-C/G1-D) est à peine au-dessus du hasard ; réduire les NFE de 40 à 12 (G1-B)
   divise la latence par ~3 mais la PR-AUC par ~2.
3. **Hypothèse H1** (« la diffusion améliore le rappel à FPR fixé d'au moins +0,05 vs la meilleure baseline non
   générative ») : **écart observé favorable sur `raw` (+0,10)**, **défavorable sur `physics` (−0,19)** ; ni confirmation ni réfutation confirmatoire puisque le seuil d'effet a été proposé après observation. ⚠ La valeur X = 0,05 n'avait
   pas été chiffrée dans la Bibliothèque V3 avant ce premier essai ; elle est proposée ici et doit être **figée par
   l'équipe avant la prochaine campagne** pour que H1 reste réfutable. Conclusion honnête : la diffusion
   apporte de la valeur quand la structure des anomalies n'est pas connue a priori ; elle ne doit pas remplacer des règles
   métier connues — elle peut les compléter (TWF/HDF).
4. **Prochaine expérience** : combiner règle physique + score diffusion (ensemble), tester un modèle de diffusion
   temporel (Diffusion-TS) sur de vraies séries si une télémétrie licite devient disponible, et calibrer le seuil par
   équipement.

## 5. Limites (à rappeler à l'oral)

- Données **synthétiques industrielles** : aucune validité pour des équipements médicaux ; pas de vraie temporalité.
- 68 pannes en test : intervalles d'incertitude larges (TWF n = 7, RNF n = 5 — RNF est aléatoire par construction).
- Une anomalie détectée ne prouve pas une panne imminente ; ce n'est pas de la « maintenance prédictive ».
- Matériel : CPU uniquement (12 cœurs logiques, PyTorch 2.x CPU) ; temps mesurés sur une machine partagée.

## 6. Les 10 cas historiques (`experiments/results/j1_cases_results.csv`)

Seuils (quantile 95 % des normaux de validation) : B0a_zscore = 2.322, B0b_isolation_forest = 0.583, G1-A_ddpm_elbo_nt10 = 0.781, G1-B_ddpm_elbo_nt3 = 0.878.

| Cas | Catégorie | B0-a z-score | B0-b IForest | G1-A DDPM 10 pas | G1-B DDPM 3 pas |
|---|---|---|---|---|---|
| J01 | normal_typique | 0.541 · ✅ | 0.460 · ✅ | 0.681 · ✅ | 0.714 · ✅ |
| J02 | normal_typique | 1.548 · ✅ | 0.458 · ✅ | 0.738 · ✅ | 0.484 · ✅ |
| J03 | normal_typique | 1.406 · ✅ | 0.444 · ✅ | 0.611 · ✅ | 0.773 · ✅ |
| J04 | normal_typique | 0.906 · ✅ | 0.425 · ✅ | 0.653 · ✅ | 0.757 · ✅ |
| J05 | normal_difficile (proche frontière HDF) | 1.085 · ✅ | 0.439 · ✅ | 0.725 · ✅ | 0.859 · ✅ |
| J06 | panne_TWF | 1.584 · ❌ | 0.431 · ❌ | 0.605 · ❌ | 0.546 · ❌ |
| J07 | panne_HDF | 1.501 · ❌ | 0.523 · ❌ | 0.639 · ❌ | 0.575 · ❌ |
| J08 | panne_PWF | 2.801 🔔 ✅ | 0.539 · ❌ | 0.623 · ❌ | 0.596 · ❌ |
| J09 | panne_OSF | 3.001 🔔 ✅ | 0.606 🔔 ✅ | 0.994 🔔 ✅ | 0.911 🔔 ✅ |
| J10 | panne_RNF | 1.296 · ❌ | 0.431 · ❌ | 0.499 · ❌ | 0.456 · ❌ |
| **Corrects** | | **7/10** | **6/10** | **6/10** | **6/10** |

🔔 = alerte (score ≥ seuil). Lecture : les 4 normaux typiques et le normal difficile ne déclenchent aucune fausse alerte ;
seules les pannes à valeurs extrêmes sont détectées (OSF par tous, PWF par la règle z-score). HDF, TWF et RNF, dont
chaque mesure reste individuellement dans la plage normale, sont manquées par toutes les méthodes au seuil 5 % FPR.
**Sur 10 cas, l'écart entre méthodes (7 vs 6/10) n'est pas interprétable** : la comparaison exploratoire plus informative est celle du test
complet (2 000 observations, 3 seeds) où G1-A double le rappel d'IForest et dépasse le z-score (docs/32_rcs71_baseline_vs_diffusion.md).

Commande : `python src/run_j1_cases.py` → `experiments/j1_diffusion/test_cases.jsonl` (définition des cas, règle de
sélection déterministe, antériorité non attestée) et `experiments/results/j1_cases_results.csv` (format commun `case_id,strategy,metric,value,unit,
evidence_status,notes` : scores, seuils, alertes et justesse par cas et par modèle, statut **mesuré**).


## 7. Revue de provenance et intégration

Le manifeste `experiments/j1_diffusion/case_inventory.json` identifie les 10 cas du commit 6506cba et le blob Git du JSONL. Il est établi après les résultats : **il ne prouve pas un gel préalable**. Le champ freeze_commit reste null. Les résultats et hypothèses sont exploratoires ; aucune approbation scientifique n'est revendiquée. Pour une campagne confirmatoire, faire approuver en équipe la règle, les variantes, les seuils et un manifeste daté avant les exécutions, conserver les preuves et reproduire sur un environnement versionné. Les résultats historiques restent intacts dans un fichier J1 distinct, sans remplacer le gabarit commun de main. Dépendances : schéma #19, ingestion #12, stockage #20 et socle J1 #14.

## 8. Reproduction rapportée et sélection déterministe (24/11, suite à la revue d'Elias)

**Reproduction** : exécution complète à partir du commit `d163e32` sur un environnement propre (`python scripts/download_ai4i.py` avec vérification SHA-256 des données, puis `python src/run_j1_diffusion.py` et `python src/run_j1_cases.py` ; Windows, Python 3.12.10, CPU). Rapport : `experiments/results/j1_reproduction_2026-11-24.json`.

| Contrôle | Résultat |
|---|---|
| PR-AUC, ROC-AUC, rappel, FPR et F1 sur les 12 lignes (2 représentations × 6 modèles, moyenne 3 seeds) | **identiques** (écart maximal 0) |
| Fichier des 10 cas régénéré par la règle | **identique** (mêmes 10 UDI, même empreinte) |
| Différences | uniquement les latences (`latency_batch10`), qui dépendent de la machine |

**Pourquoi la règle de sélection n'utilise pas les scores des modèles (sans preuve d'antériorité)** :
- la fonction `frozen_cases(df, i_test)` ne reçoit **que les données, le split et les labels** : elle n'a accès à aucun score, seuil ni résultat de modèle (vérifié par le test `test_case_selection_rule_does_not_use_model_scores`) ;
- la règle est déterministe : la relancer redonne exactement les mêmes 10 cas, ce que la reproduction confirme ;
- les seuils sont calculés sur les normaux de **validation** (`test_threshold_is_computed_on_validation_normals_only`), jamais sur le test ;
- les variantes G1-A à G1-D et leurs hyperparamètres sont fixés dans `experiments/results/j1_config.json` et identiques pour tous les cas.

**Ce qui reste vrai** : l'**antériorité** du gel (commit de gel avant toute évaluation) ne peut pas être prouvée rétroactivement ; `freeze_commit` reste `null`. Pour une campagne confirmatoire : faire approuver ce fichier de cas en équipe, renseigner `freeze_commit`, puis relancer les commandes ci-dessus après ce commit.
