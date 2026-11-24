# RCS-57 — Entraîner ou adapter un modèle de diffusion pour J1

> Reprise littérale de la fiche Jira **RCS-57** (Story, épic RCS-8, priorité High, statut « En cours »).
> Source : bibliothèque RoboCare Sentinel V3. Phase indicative **S4** ; dates, estimations, Sprint et démarrage à fixer lors de la planification.
> Responsable : **Elias** · binôme : **Ayoub** · relais : **Omar** · relectrice des critères : **Gémima**.
> Ce document est une preuve de **reproductibilité logicielle**, pas une validation scientifique ni une preuve clinique.

## 1. Objectif et critères du ticket

| Champ Jira | Contenu |
|---|---|
| Objectif | Essais contrôlés, seeds, logs, hyperparamètres, deux variantes |
| Critère d'acceptation | Exécution reproductible et outputs conservés |
| Compétence à développer | Diffusion |
| Trois volets | Contribution du pilote ; apprentissage accompagné du binôme ; recherche/veille documentée si la mission le requiert |
| En cas de blocage | Documenter obstacle, essais et liens dans le ticket ; solliciter le binôme et le relais, puis arbitrer au point de coordination |

L'attribution est approuvée collectivement ; aucune date ni estimation n'est inventée ici.

## 2. Ce que fait le code

`src/diffusion_adapter.py` implémente un **mini-DDPM 1D déterministe** en bibliothèque standard Python (`math`, `random`, `json`) : bruitage `q_sample`, prédiction du bruit par un petit réseau, et boucle de débruitage. Aucun GPU, réseau, modèle pré-entraîné, version de modèle ou licence n'est supposé.

Les **deux variantes** sont un essai contrôlé : tout est identique (données synthétiques, schedule bêta linéaire, `lr`, `epochs`, `batch_size`, seed de base), **seul le conditionnement temporel change**.

| Variante | Débruiteur | Ce qui est testé |
|---|---|---|
| `base` | MLP 1 couche cachée, entrée = signal bruité seul | référence sans conscience du pas de diffusion |
| `adapte` | même MLP, entrée = signal bruité + encodage sinusoïdal du pas `t` | adaptation du débruiteur au pas de diffusion (J1) |

Le mot « adapte » désigne ici une **variante d'entraînement J1**. Il ne désigne pas le « V2 » du TP04, qui est une orchestration J2 (mono-LLM vs routage/cascade) et **non une optimisation directe du DDPM** (cf. RCS-22).

Les hyperparamètres sont figés dans `DiffusionConfig` ; toute modification change l'empreinte `run_id`. Les deux variantes partagent la **même seed** pour que le seul facteur variable soit le conditionnement temporel. Chaque exécution consigne : seed, seed du jeu de test, pertes par époque, erreur de prédiction du bruit et erreur de reconstruction sur le jeu de test.

## 3. Commandes reproductibles

```bash
# 1. Exécuter les deux variantes et conserver les outputs
python -m src.diffusion_adapter --out experiments/results/rcs57_diffusion_variants.json

# 2. Rejouer l'expérience et vérifier la preuve d'acceptation
python -m src.diffusion_adapter --acceptance \
  --out experiments/results/rcs57_diffusion_variants.json \
  --proof-out governance/rcs57_acceptance.json

# 3. Suite de tests
python -m unittest discover -s tests -p 'test_*.py' -v
```

La commande d'acceptation recalcule les pertes et les mesures depuis le code et les compare à l'artefact conservé (tolérance relative `1e-6`). Elle vérifie neuf critères : champs du ticket, deux variantes contrôlées, seeds fixes, hyperparamètres journalisés, logs conservés, outputs conservés, rejeu déterministe, absence de résultat figé, et périmètre synthétique sans seuil de détection gelé.

## 4. Outputs conservés

| Fichier | Rôle |
|---|---|
| `src/diffusion_adapter.py` | code du mini-DDPM, des deux variantes, de la preuve et de la CLI |
| `tests/test_diffusion_adapter.py` | contrôles de déterminisme, de traçabilité et de non-invention |
| `experiments/results/rcs57_diffusion_variants.json` | configuration, seeds, logs et mesures réellement calculées |
| `governance/rcs57_acceptance.json` | preuve d'acceptation régénérée après chaque changement |

## 5. Limites et dépendances

- Signaux **entièrement synthétiques** : aucune preuve médicale ou industrielle.
- Mini-débruiteur **pédagogique**, pas un modèle SOTA ni un modèle pré-entraîné justifié.
- Aucun seuil de détection n'est gelé : il reste **ND** et doit être harmonisé puis gelé avant chaque campagne (RCS-22 / RCS-81).
- La reconstruction mesurée ne remplace pas la comparaison baseline vs diffusion sur les mêmes cas figés (RCS-69 / RCS-70 / RCS-71).
- Le passage à une génération réelle justifiée (modèle, licence, données autorisées, temps de calcul) relève de **RCS-70** ; les mesures de service et la décision GO/NO-GO restent **ND**.

## 6. Liens avec les autres tickets

- **RCS-55 / RCS-71** : comparaison exploratoire déjà exécutée dans #25 ; campagne confirmatoire sur cas préalablement gelés à réaliser.
- **RCS-56** : étude Diffusion-TS / PhysDiff, licences et capacité GPU.
- **RCS-69 / RCS-70** : cas gelés puis exécution diffusion réelle.
- **RCS-22 / RCS-81** : protocole J1 vs J2, métriques distinctes, seuils gelés avant campagne.


## 7. Articulation des trois implémentations J1 (revue du 24/11)

| Contribution | Rôle | Périmètre de preuve |
|---|---|---|
| PR #7 (RCS-70) | DDPM NumPy sur signaux synthétiques, apprentissage et reconstruction | Démonstrateur pédagogique intégré à main |
| PR #38 (RCS-57) | Mini-DDPM 1D en bibliothèque standard, comparaison contrôlée du conditionnement temporel | Reproductibilité logicielle synthétique, deux variantes |
| PR #25 (RCS-71) | DDPM tabulaire PyTorch vs z-score/Isolation Forest sur AI4I industriel, ablations | Comparaison exploratoire B/C sur le même jeu industriel ; pas de preuve biomédicale |

La PR #25 est la référence pour la comparaison exploratoire baseline/diffusion. Son artefact de reproduction du 24/11 (commit b638aea, `experiments/results/j1_reproduction_2026-11-24.json`) rapporte les métriques de qualité identiques après rejeu. Ce n'est pas un gel préalable : `freeze_commit` reste null. Les deux démonstrateurs synthétiques ne sont pas des implémentations concurrentes du benchmark. Ne pas mélanger leurs métriques, données et hypothèses. Un choix de modèle et une campagne confirmatoire distincte doivent être validés en équipe.
