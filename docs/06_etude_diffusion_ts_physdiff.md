# RCS-56 — Étude Diffusion-TS et PhysDiff

> **Statut : veille technique avec licences vérifiées le 2026‑11‑23 et environnement local mesuré le 2026‑11‑24 ; aucune validation expérimentale revendiquée.** Les cases cochées ci-dessous concernent l'analyse documentaire et la mesure d'environnement, pas l'exécution d'un modèle. La disponibilité CUDA locale est `ND` (voir « Preuve d'environnement ») ; le jeu de données reste `ND`.

## Fiche 1 — Diffusion-TS

| Champ | Contenu |
|---|---|
| Référence | Yuan & Qiao, *Diffusion-TS: Interpretable Diffusion for General Time Series Generation*, ICLR 2024. arXiv:2403.01742. Repo: https://github.com/Y-debug-sys/Diffusion-TS |
| Type | Modèle de diffusion pour séries temporelles (génération/interprétation) |
| Problème ciblé | Génération de séries temporelles réalistes, avec décomposition tendance/saisonnalité/bruit |
| Données/entrées | Séries temporelles multivariées/univariées selon config dataset |
| Sorties | Séries synthétiques / reconstructions selon tâche |
| Intérêt pour RoboCare | Génération/reconstruction de signaux capteurs pour J1, augmentation prudente, analyse d'écarts |
| Limites | Pas spécifique biomédical; nécessite adaptation données, évaluation rigoureuse, coût compute; risque d'artefacts |
| Licence | **MIT — vérifié le 2026‑11‑23** via le fichier `LICENSE` et le badge du README officiel (https://github.com/Y-debug-sys/Diffusion-TS/blob/main/LICENSE). Le copyright amont est indiqué « XXX » : conserver la mention telle quelle en cas de réutilisation. |
| Faisabilité POC | Moyenne : code public et licence confirmée, mais **GPU CUDA requis**, Python 3.8 / PyTorch 2.0 selon le README officiel, et données autorisées nécessaires ; smoke test petit modèle envisageable après validation environnement |
| Prérequis | conda/venv, PyTorch 2.0, dataset temporel autorisé/synthétique, pipeline preprocessing, métriques temporelles, GPU CUDA |
| Risques | Biais de données, fuite de distribution, surinterprétation clinique, coût GPU |
| Décision provisoire | **Priorité 1 pour l'étude J1**, sous réserve GPU/données ; smoke test uniquement, aucune intégration de code faite ici |

### Critères d'acceptation RCS-56 (Diffusion-TS)

- [x] Fiche critique complétée (source, licence, hypothèses, limites)
- [x] Vérification licence/droits d'usage — MIT confirmé sur le dépôt officiel
- [x] Évaluation capacité GPU/environnement — mesurée le 2026‑11‑24, preuve : [`governance/rcs56_gpu_capacity.json`](../governance/rcs56_gpu_capacity.json) (CUDA `ND`, torch absent localement)
- [x] Plan de faisabilité documenté (smoke test, métriques, risques) — voir ci-dessous ; GPU évalué dans la « Preuve d'environnement »

## Fiche 2 — PhysDiff

| Champ | Contenu |
|---|---|
| Référence | Yuan et al., *PhysDiff: Physics-Guided Human Motion Diffusion Model*, ICCV 2023 (Oral). arXiv:2212.02500. Page projet : https://nvlabs.github.io/PhysDiff/ . Code auteur : https://github.com/umariqb/PhysDiff |
| Type | Diffusion guidée par contraintes physiques (mouvement humain) |
| Problème ciblé | Génération de mouvements physiquement plausibles (pénétration sol, flottement, etc.) |
| Données/entrées | Données de mouvement humain / représentations 3D selon papier |
| Sorties | Séquences de mouvement générées avec contrainte physique |
| Intérêt pour RoboCare | Intérêt méthodologique : ajouter contraintes domaine/physique à une diffusion; transposition directe aux signaux biomédicaux non évidente |
| Limites | Domaine différent (motion capture) ; pas directement applicable aux signaux d'équipements médicaux sans reformulation complète |
| Licence | **Non déclarée — vérifié le 2026‑11‑23** : l'API GitHub du dépôt officiel `umariqb/PhysDiff` renvoie `license: null`, aucun fichier `LICENSE` n'est présent, et la page projet/arXiv ne précisent pas la licence du code (seul l'article est sous licence arXiv `nonexclusive-distrib`). Droits d'usage **non confirmés** : ne pas intégrer ni copier de code sans clarification écrite. |
| Faisabilité POC | Faible à moyenne pour RoboCare J1 : forte adaptation nécessaire, et blocage licence tant qu'elle n'est pas déclarée |
| Prérequis | Compréhension du domaine, reformulation des contraintes physiques biomédicales, données adaptées, clarification licence |
| Risques | Mauvaise transposition domaine, coût ingénierie élevé, faux sentiment de robustesse, incertitude juridique sur le code |
| Décision provisoire | **NO-GO pour intégration code** ; veille méthodologique uniquement. |

### Critères d'acceptation RCS-56 (PhysDiff)

- [x] Fiche critique complétée
- [x] Analyse de transposibilité au domaine RoboCare — faible, nécessite reformulation complète
- [x] Vérification licence/droits effectuée — résultat : **licence code non déclarée** (voir ci-dessus)
- [x] Conclusion GO/NO-GO pour POC — **NO-GO intégration** ; garder comme référence méthodologique seulement

## Plan de faisabilité comparé

| Axe | Diffusion-TS | PhysDiff |
|---|---|---|
| Pertinence RoboCare J1 | Élevée (séries temporelles) | Faible/méthodologique |
| Effort d'adaptation | Moyen | Élevé |
| Données nécessaires | Séries temporelles autorisées | Données motion/contraintes, reformulation |
| GPU requis | Oui (README officiel, CUDA) | Probable + pipeline spécifique |
| Licence code | MIT (confirmée) | Non déclarée (bloquante) |
| Risque principal | Mauvaise généralisation / artefacts | Hors domaine / transposition invalide / droits non confirmés |
| Recommandation | Priorité 1 pour étude J1, sous réserve GPU + données | Priorité 2 (veille), NO-GO intégration |

## Preuves de vérification (2026-11-23)

- Diffusion-TS : `https://github.com/Y-debug-sys/Diffusion-TS/blob/main/LICENSE` (MIT) et README officiel (badge licence, Python 3.8, PyTorch 2.0, « one CUDA capable GPU »).
- PhysDiff : `https://api.github.com/repos/umariqb/PhysDiff` (`"license": null`), absence de `LICENSE` à la racine, `https://nvlabs.github.io/PhysDiff/` et `https://arxiv.org/abs/2212.02500` (licence article uniquement).
- Aucun code de ces dépôts n'a été copié dans ce dépôt.

## Preuve d'environnement (2026‑11‑24)

Mesure produite par `experiments/check_diffusion_environment.py` (bibliothèque standard uniquement) et conservée dans [`governance/rcs56_gpu_capacity.json`](../governance/rcs56_gpu_capacity.json).

| Élément | Valeur mesurée |
|---|---|
| Python | 3.15.0 |
| Système / machine | Windows / AMD64 |
| `torch_available` | `false` (détection par `find_spec`) |
| `cuda_available` | `ND` (torch absent : aucun import CUDA tenté localement) |
| `gpu_count` / `gpu_name` | `ND` / `ND` |
| numpy / sklearn / pandas | disponibles (détection par `find_spec`) |
| Smoke test Diffusion-TS local | **NO-GO** — « CUDA ND/non disponible localement » |
| Mini-DDPM stdlib (RCS-57) | **GO** — aucun GPU requis |

La sonde torch est bornée à 15 secondes dans un sous-processus : un import lent ou défaillant est enregistré comme `ND`. Le script ne relève ni pilote, ni coût, ni licence, et n'invente aucun GPU. Les vérifications de licence ci-dessus restent inchangées.

**Décision :** NO-GO pour le smoke test Diffusion-TS sur cette machine tant que CUDA n'est pas disponible ; la veille et la préparation des données restent possibles. La poursuite expérimentale locale passe par un mini-DDPM en bibliothèque standard (RCS-57), sans GPU. Aucune échéance, version de modèle, licence, coût ou résultat d'entraînement n'est affirmé ici.

## Prochaines actions

1. [x] Vérifier licences et conditions d'usage : MIT pour Diffusion-TS ; non déclarée pour PhysDiff.
2. [ ] Identifier un dataset temporel autorisé/synthétique pour smoke test Diffusion-TS.
3. [x] Évaluer la capacité GPU locale : [preuve conservée](../governance/rcs56_gpu_capacity.json) — CUDA `ND`, smoke test Diffusion-TS local en NO-GO.
4. [ ] Définir métriques J1 : reconstruction, détection, faux positifs/négatifs, coût, reproductibilité.
5. [ ] Demander clarification de licence à l'équipe PhysDiff uniquement si un besoin méthodologique précis apparaît.
6. [ ] Ne lancer aucun entraînement lourd sans validation données/GPU/budget.
7. [ ] Poursuivre la voie locale sans GPU via le mini-DDPM stdlib (RCS-57), en s'appuyant sur la preuve d'environnement ci-dessus.
