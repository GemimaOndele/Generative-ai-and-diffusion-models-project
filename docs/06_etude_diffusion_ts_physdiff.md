# RCS-56 — Étude Diffusion-TS et PhysDiff

> **Statut : veille technique à compléter.** Vérifier licences, dates, versions, et faisabilité réelle avant toute intégration. Ne pas présenter ces fiches comme une validation expérimentale.

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
| Licence | À vérifier sur le repo officiel avant usage (ne pas présumer compatible) |
| Faisabilité POC | Moyenne : code public annoncé, mais dépendances GPU/données/prétraitement à valider |
| Prérequis | PyTorch, dataset temporel autorisé, pipeline preprocessing, métriques temporelles |
| Risques | Biais de données, fuite de distribution, surinterprétation clinique, coût GPU |
| Décision provisoire | **À tester en smoke test** uniquement après vérification licence/données |

### Critères d'acceptation RCS-56 (Diffusion-TS)
- [ ] Fiche critique complétée (source, licence, hypothèses, limites)
- [ ] Vérification licence/droits d'usage
- [ ] Évaluation capacité GPU/environnement
- [ ] Plan de faisabilité (smoke test, métriques, risques)

## Fiche 2 — PhysDiff

| Champ | Contenu |
|---|---|
| Référence | Yuan et al., *PhysDiff: Physics-Guided Human Motion Diffusion Model*, ICCV 2023. arXiv:2212.02500. Site/projet: https://nvlabs.github.io/PhysDiff/ |
| Type | Diffusion guidée par contraintes physiques (mouvement humain) |
| Problème ciblé | Génération de mouvements physiquement plausibles (pénétration sol, flottement, etc.) |
| Données/entrées | Données de mouvement humain / représentations 3D selon papier |
| Sorties | Séquences de mouvement générées avec contrainte physique |
| Intérêt pour RoboCare | Intérêt méthodologique : ajouter contraintes domaine/physique à une diffusion; transposition directe aux signaux biomédicaux non évidente |
| Limites | Domaine différent (motion capture) ; pas directement applicable aux signaux d'équipements médicaux sans reformulation complète |
| Licence | À vérifier (code/assets NVIDIA/projet) avant usage |
| Faisabilité POC | Faible à moyenne pour RoboCare J1 : forte adaptation nécessaire |
| Prérequis | Compréhension du domaine, reformulation des contraintes physiques biomédicales, données adaptées |
| Risques | Mauvaise transposition domaine, coût ingénierie élevé, faux sentiment de robustesse |
| Décision provisoire | **Veille méthodologique** ; ne pas prioriser pour POC J1 immédiat sauf contrainte physique claire |

### Critères d'acceptation RCS-56 (PhysDiff)
- [ ] Fiche critique complétée
- [ ] Analyse de transposabilité au domaine RoboCare
- [ ] Vérification licence/droits
- [ ] Conclusion GO/NO-GO pour POC

## Plan de faisabilité comparé

| Axe | Diffusion-TS | PhysDiff |
|---|---|---|
| Pertinence RoboCare J1 | Élevée (séries temporelles) | Faible/méthodologique |
| Effort d'adaptation | Moyen | Élevé |
| Données nécessaires | Séries temporelles autorisées | Données motion/contraintes, reformulation |
| GPU requis | Probable (smoke test possible petit modèle) | Probable + pipeline spécifique |
| Risque principal | Mauvaise généralisation / artefacts | Hors domaine / transposition invalide |
| Recommandation | Priorité 1 pour étude J1 | Priorité 2 (veille) |

## Prochaines actions

1. Vérifier licences et conditions d'usage des repos officiels.
2. Identifier un dataset temporel autorisé/synthétique pour smoke test Diffusion-TS.
3. Définir métriques J1 : reconstruction, détection, faux positifs/négatifs, coût, reproductibilité.
4. Ne lancer aucun entraînement lourd sans validation données/GPU/budget.
