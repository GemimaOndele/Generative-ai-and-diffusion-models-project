# RoboCare Sentinel — plateforme web d'assistance à la maintenance biomédicale

**ECE Paris · MSc2 Artificial Intelligence · Projet fil rouge**  
Équipe : **Gémima, Aminata, Omar, Elias et Ayoub**.  
**État vérifié au 20 novembre 2026 : cadrage, organisation et preuves préparatoires.** Aucune validation clinique, aucun POC diffusion ou benchmark Multi-LLM réel n'est revendiqué par ce README.

## À quoi servira la plateforme ?

Centraliser des informations techniques autorisées sur **une famille pilote de dispositifs médicaux encore à sélectionner** : inventaire, ingestion et qualité, détection d'anomalies expérimentale, alertes soumises à un technicien biomédical, assistance documentaire sourcée et suivi des interventions. **Aucune commande ni réparation automatique de machines réelles.** Les données industrielles ou simulées ne démontrent pas une efficacité hospitalière.

Le projet unit l'application et deux jalons :
- **J1 GenAI/diffusion :** générer/reconstruire des signaux avec un modèle réel et comparer à une baseline ML sur des cas gelés.
- **J2 Multi-LLM/Green AI :** assistance RAG, mono-A/mono-B vs routing/cascade, évaluation équitable de la qualité, des citations, des erreurs, du coût complet, de la latence p95 et des limites environnementales.

## Instructions et preuves pédagogiques

| Consigne | Temps de séance | Tickets | Artefacts attendus / statut |
|---|---|---|---|
| CM03 — preuve GenAI C3 | 60 min | RCS-69–73 | `docs/03_preuve_technique.md`, `tests/cases.csv`, `experiments/results.csv`, seed, logs ; **non exécuté** |
| TP04 — deux vrais LLM | 120 min + 30 min facultatives | RCS-74–80 | `docs/05_tp04_architecture_v2.md`, `src/orchestrator.py`, `experiments/test_cases.jsonl`, benchmark ; **non mesuré** |
| TP05 — FinOps, Green AI, Éthique | 90 min, complète J2 | RCS-81–86 | `docs/06_tp05_finops_green_ethique.md`, journal coût/qualité, CodeCarbon **local facultatif**, audit éthique ; **résultats ND** |
| Gouvernance continue | Toutes les phases | RCS-18, 65, 66, 78, 83–90 | Cartographie versions et risques/biais, registre de coûts/temps, traces et runbook ; **schémas préparés, à valider** |

**ND = non disponible/non mesuré**, pas égal à zéro. Un exercice de bruitage seul ne prouve pas un détecteur entraîné ; une simulation/mocking ne prouve pas la qualité d'un LLM ; CodeCarbon local ne mesure pas les serveurs du fournisseur d'API distante.

## Documents, dossiers et état des branches

Ce dépôt a été initialisé progressivement. **Les fichiers ci-dessous sont dans des Pull Requests et peuvent ne pas être visibles dans `main` tant qu'elles ne sont pas fusionnées.**

| PR | Branche temporaire existante | Contenu | État au 20/11 |
|---|---|---|---|
| [#1](../../pull/1) | `docs/RCS-46-structure-projet` | Structure `frontend/`, `backend/`, `src/`, `models/`, `db/`, `docs/`, `data/`, `experiments/`, `tests/`, CI, `CONTRIBUTING.md` | Ouverte, en attente des quatre revues |
| [#2](../../pull/2) | `docs/RCS-17-sprint0-c3-tp04-preparation` | Sprint 0, protocoles C3/TP04, 10 cas fictifs proposés **non gelés** | Brouillon |
| [#3](../../pull/3) | `docs/RCS-81-tp05-finops-green-ethique` | Rapport TP05, CodeCarbon local facultatif, sécurité, tests de parseur | Brouillon |
| [#4](../../pull/4) | `docs/RCS-87-cartographie-versioning-risques-couts` | Versions, model/dataset cards, biais, coûts humain/infra, risque, observabilité et trace_event | Brouillon |

Le dossier `governance/` et les documents `docs/10` à `docs/13` sont proposés dans **la PR #4** ; leurs registres CSV sont volontairement vides. Le fichier `docs/00_reference_index.md` récapitule les références et chemins prévus.

## Qui fait quoi ?

| Membre | Rôle de référence | Travail de préparation prioritaire |
|---|---|---|
| **Gémima** | Coordination Jira/Drive, métier-données, risques/coûts | Sprint 0 RCS-17 ; cadrage C3 RCS-69 ; coût complet RCS-90 |
| **Aminata** | Analyse fonctionnelle, parcours, documentation, éthique | Jeux TP04 RCS-74 ; audit RCS-84 ; biais avec Elias RCS-88 |
| **Omar** | Data Engineering, JMerise, baselines, coûts | DoR/DoD RCS-16 ; baseline RCS-71 ; coûts RCS-82 et binôme RCS-90 |
| **Elias** | Diffusion, Multi-LLM, métriques, biais | Modèles A/B RCS-75 ; diffusion RCS-70 ; model cards RCS-88 |
| **Ayoub** | Architecture web, intégration, GitHub/CI, monitoring | Revue PR #1 RCS-46/48 ; cartographie RCS-87 ; traces RCS-89 |

Les tâches RCS-81–90 ont été attribuées **à titre de proposition à ratifier**. Les 52 tâches historiques sont approuvées. Le Sprint 0 est **futur, non démarré et non estimé** ; toute charge/délais doit être validée par le groupe.

## GitHub et Jira : une branche par ticket, pas par personne

Les cinq membres peuvent utiliser le dépôt avec leurs comptes existants. `main` est **protégée** (PR obligatoire, une approbation, CI, discussions résolues, pas de suppression/force push). Personne n'a de branche personnelle attitrée.

1. Sélectionner une mission [Jira RCS](https://gemimakerenondelepourou.atlassian.net/jira/software/projects/RCS/boards/1/backlog), désigner pilote, binôme, relais, relecteur et critères.
2. Quand le travail est prêt, créer depuis `main` une branche `feature/RCS-XX-sujet`, `experiment/RCS-XX-sujet`, `data/RCS-XX-sujet`, `docs/RCS-XX-sujet` ou `fix/RCS-XX-sujet`.
3. Committer du code/documents vérifiables, ouvrir une PR vers `main`, lier le ticket Jira, faire relire par une **autre personne**, corriger et vérifier la CI.
4. **Après une fusion validée**, supprimer normalement la branche temporaire si aucun travail non fusionné n'y reste. L'historique des commits et la PR restent conservés. Pour une version stable, utiliser un tag/release et le registre de modèles.
5. Pour une nouvelle tâche, créer une nouvelle branche depuis un `main` mis à jour. **Ne pas créer des branches permanentes par membre.**

Voir [les conventions](CONTRIBUTING.md) (PR #1) et [le modèle de PR](.github/pull_request_template.md) (PR #1). Après fusion de PR #1, harmoniser les README des PR #2 à #4 avant fusion pour éviter tout écrasement.

## Cartographie, risques, coûts et traçabilité : dès le départ

- Cartographie `source → dataset + hash/licence → modèle/version → prompt/corpus → API → interface → humain`, associée à `run_id`, `trace_id` et SHA Git.
- **Model/dataset cards** : données, couverture/angles morts, faux positifs et négatifs, biais, sous-groupes autorisés et limites de transfert industriel→médical.
- Registre risques : probabilité, impact, déclencheur, personne concernée, mitigation, risque résiduel et responsable ; revue à chaque Sprint/changement important.
- FinOps continu : **€ payés, heures réellement consacrées, coûts d'infrastructure, supervision humaine valorisée sous hypothèse distincte** ; coût par tâche correctement traitée uniquement sur mesures et tarifs sourcés.
- Monitoring : disponibilité, qualité, dérive, citations/refus, p95, appels/retries, coûts, incidents, énergie locale estimée via CodeCarbon, serveur API distant **ND** ; limiter les traces aux métadonnées non sensibles.

**Sécurité :** pas de données patients ni documents non autorisés, secrets API, mots de passe, poids ou datasets lourds dans le dépôt. Ne jamais revendiquer une conformité réglementaire ou une validation clinique sans preuve.

## Référentiel documentaire et sources

Les versions complètes destinées au **Drive partagé** sont : **fiche d'équipe V5.0, bibliothèque V3.6, cahier des charges V1.3**. Le Drive fait foi après approbation du groupe ; les README/PR GitHub servent à la traçabilité et au code.

Sources pédagogiques ECE Paris : *CM03 première preuve GenAI*, *TP04 intégration Multi-LLM* (17/11/2026), *TP05 FinOps/Green AI/Éthique* et le cours associé (20/11/2026). Les remarques orales rapportées par le groupe sur versions, biais, risques et coûts sont différenciées des exigences attestées dans les PDF.

Documentation externe utile : [CodeCarbon](https://docs.codecarbon.io/latest/), [FinOps Foundation](https://www.finops.org/).

**Prochaine porte de passage :** revue collective de PR #1 et des nouvelles responsabilités, capacité et données autorisées validées, puis lancement explicite du Sprint 0 avec des preuves expérimentales réelles.
