# TP04 — protocole préparatoire de benchmark Multi-LLM (RCS-74 à RCS-79)

> **Statut : préparation, aucun test de LLM réel exécuté.** Le jeu `experiments/tp04_cases_draft.jsonl` contient **10 cas fictifs** rédigés pour discussion. Il est **NON GELÉ** et doit être validé par le groupe avant de devenir `experiments/test_cases.jsonl`. N'utiliser ni ces réponses attendues ni ces catégories pour ajuster la politique de routage après le gel.

## Exigence pédagogique (ECE, TP04 du 17 novembre 2026)
Un modèle A seul (mono-A) et si possible B seul (mono-B) ; choisir une stratégie V2 justifiée (routing, cascade, critique, composition), comparer à jeu identique, tracer erreurs, latence, modèle, coût si connu et raison du routage ; décider GO/NO-GO. Temps de séance **120 min + 30 min facultatives**, distinct d'une estimation du travail réel du groupe.

## Jeu candidat : 10 scénarios, 4 cas de stress
- **T01–T04** : questions usuelles sur des documents pédagogiques fictifs ;
- **T05–T06** : combiner des sources et identifier la limite de l'information ;
- **T07** : source absente → abstention et demande de notice autorisée ;
- **T08** : deux sources contradictoires → arbitrage humain, pas de recommandation automatique ;
- **T09** : injection hostile insérée **dans la source** → ne pas obéir à l'instruction externe ;
- **T10** : demande de données sensibles → refus / contrôle des droits.

La source de chaque extrait est marquée **fictive**. Les appareils E-DEMO ne sont pas une famille de dispositifs retenue pour le projet et les résultats ne constitueront pas une validation médicale.

## Grille pré-écrite avant mesures
1 = succès métier selon la règle ; 0 = échec ; **NM = non mesuré**. Noter séparément qualité des citations, abstention/refus correct, robustesse par sous-groupe. Aucun score dans les données de test n'est une mesure. Après validation de la grille, figer un hash/commit du jeu de tests.

## Quatre stratégies sur les mêmes cas
| Stratégie | Qualité | p50 / p95 | Taux d'échec | Coût (si connu) | Énergie/CO₂e |
|---|---|---|---|---|---|
| mono-A | NM | NM | NM | NM | NM |
| mono-B | NM | NM | NM | NM | NM |
| routing A/B | NM | NM | NM | NM | NM |
| cascade A→B | NM | NM | NM | NM | NM |

Le routeur et le validateur ne doivent pas consulter `expected` pendant l'inférence. Pour chaque appel : `case_id` et hash, modèle exact/version, stratégie, raison de la route, heure/durée, timeout/statut/type d'erreur, tokens, nombre d'appels, coût (ou `null`) et décision finale. Ne pas enregistrer des prompts contenant des données sensibles.

## Portes avant exécution live
- C3 V1 ou prototype mono-LLM existant **réellement** documenté ; sinon documenter cette dépendance manquante.
- Deux modèles de langage réellement distincts, version, fournisseur, licence, lieu de traitement, coût/plafond, conformité.
- Autorisation de la dépense et environnement avec clés **hors Git**.
- Règles `valid_schema`, `grounded`, `privacy_authorizes` et `budget_exceeded` réellement codées/testées, y compris refus et arrêts bornés.
- Corpus et tests gelés séparés du développement, sans source hospitalière non autorisée.

En absence d'API : démontrer les chemins logiciels hors ligne et journaliser le blocage ; **ne jamais** qualifier un mock de benchmark LLM. Green AI : énergie **mesurée** seulement si instrumentation locale suffisante, sinon **estimée** avec hypothèses et incertitude ou **non disponible**. Pas d'inférence depuis les prix API.

## Livrables finaux à produire après expériences
`docs/05_tp04_architecture_v2.md`, `src/orchestrator.py`, `experiments/test_cases.jsonl`, `experiments/results/tp04_*.csv/jsonl`, `docs/05_tp04_benchmark.md`, `data/manifest.md` et `README.md`. Le dossier de préparation ne se substitue pas à ces livrables.
