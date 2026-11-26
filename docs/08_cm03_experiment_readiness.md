# C3 — Porte d'entrée avant la première preuve diffusion (RCS-69 à RCS-73)

> **Préparation uniquement, zéro expérience de diffusion déclarée.** Support CM03 ECE : **60 minutes** structurées en 5 séquences ; cela n'est ni une échéance Jira ni une preuve que la séance a été effectuée.

## Décisions préalables
1. **Modalité :** série temporelle ou autre, justifiée par le domaine de maintenance étudié ;
2. **Source :** vérifier licence, volume, vérité terrain et différence industriel vs biomédical (RCS-19 / RCS-25 / RCS-27) ;
3. **Jeu de test :** 8–10 exemples représentatifs, difficultés et négatifs ; séparer train/validation/test, éviter une fuite de labels ;
4. **Baseline :** règles/seuil/Isolation Forest ou autre adaptée à la modalité, protocole identique au candidat ;
5. **Véritable diffusion :** q_sample peut être un exercice introductif, pas une preuve qu'un modèle débruiteur est entraîné ni qu'il détecte des anomalies.

## Déroulé scientifique de 60 min
| Phase | Action | Preuve minimale |
|---|---|---|
| 00–10 min | Geler 8–10 cas et attendus | `tests/cases.csv` ou .json, traçabilité |
| 10–25 min | Génération/reconstruction minimale réelle | seed, modèle/version, sortie, trace |
| 25–40 min | Même échantillon testé sur baseline C2 | `experiments/results.csv`, métrique |
| 40–55 min | Un échec et une limite reproductibles | conditions, hypothèse de correction |
| 55–60 min | Décider prochaine expérience et versionner | `docs/03_preuve_technique.md`, README, commit |

**À ne pas inventer :** source hospitalière, étiquette de panne, supériorité de diffusion, exactitude/énergie/CO₂e sans mesure, preuve d'apprentissage à partir du seul bruitage. Séparer journal de découverte et jeu de test gelé.

## Préparation compatible avec Sprint 0
Le Sprint 0 vise **choix de la modalité/données et préparation de la grille**, pas à annoncer un modèle entraîné. Les scripts et résultats viendront lorsque le groupe aura validé la source et ses droits. RCS-69 est le point d'entrée ; RCS-70 à RCS-73 concernent la séance et les preuves techniques effectives.

## Décision GO/NO-GO (non prise)
- **GO** si données autorisées, test valide et modèle réellement génératif exécutable ;
- **NO-GO / repli expérimental** si accès, licence, labels ou ressources insuffisants ; communiquer l'écart de domaine au professeur.
