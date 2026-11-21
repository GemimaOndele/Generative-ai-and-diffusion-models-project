# RoboCare Sentinel

**Projet fil rouge — ECE Paris · MSc2 Artificial Intelligence**  
**Domaines :** IA générative, modèles de diffusion, Multi-LLM / Green AI, maintenance d'équipements médicaux.  
**Équipe :** Gémima, Aminata, Omar, Elias, Ayoub.

> **État : cadrage / préparation.** Ce dépôt ne contient pas encore de résultat scientifique validé ni d'application médicale opérationnelle. Il ne doit pas être utilisé pour diagnostiquer des patients ou commander un équipement médical réel.

## Démonstration locale RCS-38 (branche de PR #8)

Ouvrir `RoboCare-Sentinel.code-workspace` dans Cursor, puis utiliser les tâches
RCS-38 du menu Terminal → Run Task, ou lancer depuis la racine :

```bash
python -m tools.rcs38_demo_server --port 8000 --db .local/rcs38.sqlite3
```

Ouvrir http://127.0.0.1:8000/ . Python 3.11+ suffit pour l'API et SQLite ; aucun
service cloud, clé API ou paquet Python tiers n'est nécessaire à ce prototype.
La base locale conserve les décisions simulées. Pour une nouvelle session de
démonstration sans effacer la précédente, choisir un autre chemin `--db`.
Arrêter le serveur avec Ctrl+C avant de relancer la tâche sur le même port.

Le [compte rendu des vérifications locales](docs/20_verification_locale_2026-11-21.md)
précise les tests, limites et revues restant nécessaires.

## Objectif

Concevoir et développer une **plateforme web d'aide à la maintenance biomédicale** pour centraliser des informations techniques autorisées, visualiser des mesures et signalements, détecter des anomalies, préparer des interventions documentées et laisser **la décision finale au technicien**.

Deux axes scientifiques complémentaires alimentent la même application :
- **J1 – Generative AI / diffusion :** expérimenter génération/reconstruction de signaux, comparer à une baseline et analyser les limites.
- **J2 – Multi-LLM / Green AI :** comparer mono-LLM et orchestration de deux modèles réellement distincts sur les mêmes cas, avec qualité, latence, coût et énergie/CO₂e lorsque mesurables.

**Périmètre pilote, datasets, architecture détaillée et critères d'acceptation :** à valider collectivement. Des benchmarks industriels ou données simulées ne démontrent pas l'efficacité sur des machines médicales réelles.

## Pilotage du projet

- [Jira RoboCare Sentinel (RCS)](https://gemimakerenondelepourou.atlassian.net/jira/software/projects/RCS/boards/1/backlog)
- GitHub : un seul dépôt, une branche `main` de référence, branches de travail par ticket et Pull Requests relues.
- Référents : Gémima (coordination), Aminata (fonctionnel), Omar (données/JMerise), Elias (IA), Ayoub (architecture/intégration). Chaque tâche Jira précise son responsable, son binôme d'apprentissage, son relais et son relecteur.
- [RCS-46](https://gemimakerenondelepourou.atlassian.net/browse/RCS-46) : organisation du dépôt ; [RCS-47](https://gemimakerenondelepourou.atlassian.net/browse/RCS-47) : premier commit documentaire ; [RCS-48](https://gemimakerenondelepourou.atlassian.net/browse/RCS-48) : branches et PR.

## Rendus pédagogiques à intégrer (non réalisés à ce stade)

**CM03 / C3 — preuve GenAI (60 min)** : 8–10 cas figés, chaîne générative réelle, comparaison baseline, échec analysé, paramètres/seed, preuve reproductible, `docs/03_preuve_technique.md`, `tests/cases.csv`, `experiments/results.csv` et README (RCS-69 à RCS-73).

**TP04 / C4 — Multi-LLM (120 min + 30 min facultatives)** : 10 cas dont quatre stress, modèles A/B identifiés, mono-A / mono-B / V2 comparés, stratégie routing ou cascade, traces et erreurs, GO/NO-GO, `docs/05_tp04_architecture_v2.md`, `docs/05_tp04_benchmark.md`, `src/orchestrator.py`, `experiments/test_cases.jsonl`, `experiments/results/tp04_*.csv` et `data/manifest.md` (RCS-74 à RCS-80).

**Important :** un mock teste l'orchestration, jamais la qualité d'un modèle de langage ; une opération de bruitage isolée ne suffit pas à prouver la détection d'anomalies par diffusion. Aucune mesure ou résultat ne doit être inventé.

## Collaboration et sécurité

Consulter les conventions sur la branche de préparation documentaire, une fois la Pull Request relue. Ne jamais versionner des clés API, données personnelles/patients, rapports hospitaliers non autorisés, modèles ou jeux de données lourds sans validation. Décrire provenance, licence et limites des données utilisées.

## Sources pédagogiques

- ECE Paris, **CM03 — Projet final Cours 3 : première preuve GenAI**, 14 novembre 2026.
- ECE Paris, **TP04 — Du POC GenAI V1 à une V2 Multi-LLM démontrable**, 17 novembre 2026.
- Bibliothèque RoboCare Sentinel V3.4 et cahier des charges V1.1 (documents collaboratifs du groupe).

*Dernière étape du Sprint 0 avant développement : revue collective des fichiers de cadrage, des tests prévus, des accès et de la politique de collaboration.*
